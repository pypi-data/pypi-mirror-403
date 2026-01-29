# ----------------------------------------------------------------------------
# Copyright (c) Omnissa, LLC. All rights reserved.
# This product is protected by copyright and intellectual property laws in the
# United States and other countries as well as by international treaties.
# ----------------------------------------------------------------------------

from dataclasses import dataclass
import shlex
from typing import Optional, Union

from ohcs.common.utils import PluginException
from ohcs.lcm.api import Pool, VmInfo, PowerState
import os
import re
import subprocess
from threading import Lock
import logging
from yumako.lru import LRUDict
import base64

log = logging.getLogger(__name__)


@dataclass
class VmHolder:
    custom_data: str
    power_state: str
    info: Optional[VmInfo] = None


@dataclass
class PoolHolder:
    pool: Pool
    last_vars: str
    last_template: str
    pool_dir: str
    vms: dict[str, VmHolder]
    vm_resource_type_name: str = ""  # The terraform resource type name, varies from provider to provider.


_initialized = False
_pool_cache = LRUDict[str, PoolHolder](capacity=100)
_pool_lock = Lock()


class VmsAutoTfvarsFile:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.hcs_group_id: str = ""
        self.vms: dict[str, VmHolder] = {}

    def load(self) -> bool:
        """Load and parse the vms.auto.tfvars file."""
        if not os.path.exists(self.file_path):
            return False

        with open(self.file_path, "r") as f:
            content = f.read()

        # Parse hcs_group_id
        group_match = re.search(r'hcs_group_id\s*=\s*"([^"]*)"', content)
        if group_match:
            self.hcs_group_id = group_match.group(1)

        # Parse vms map
        vms_match = re.search(r"vms\s*=\s*\{([^}]*)\}", content, re.DOTALL)
        if vms_match:
            vms_content = vms_match.group(1)
            # Find all VM entries like "vm-1" = { ... }
            vm_pattern = r'"([^"]+)"\s*=\s*\{([^}]*)\}'
            for vm_match in re.finditer(vm_pattern, vms_content):
                vm_id = vm_match.group(1)
                vm_block = vm_match.group(2)

                # Extract custom_data and power_state
                custom_data_match = re.search(r'custom_data\s*=\s*"([^"]*)"', vm_block)
                power_state_match = re.search(r'power_state\s*=\s*"([^"]*)"', vm_block)

                custom_data = custom_data_match.group(1) if custom_data_match else ""
                power_state = power_state_match.group(1) if power_state_match else "off"
                self.vms[vm_id] = VmHolder(
                    custom_data=custom_data,
                    power_state=power_state,
                    info=VmInfo(
                        id=vm_id, powerState=PowerState.PoweredOn if power_state == "on" else PowerState.PoweredOff
                    ),
                )
        return True

    def write(self) -> None:
        """Write the current state to vms.auto.tfvars file."""
        content_lines = [f'hcs_group_id = "{self.hcs_group_id}"', "vms = {"]

        for vm_id, vm_data in self.vms.items():
            content_lines.append(f'  "{vm_id}" = {{')
            content_lines.append(f'    custom_data = "{vm_data.custom_data}"')
            content_lines.append(f'    power_state = "{vm_data.power_state}"')
            content_lines.append("  }")

        content_lines.append("}")

        content = "\n".join(content_lines) + "\n"

        with open(self.file_path, "w") as f:
            f.write(content)


def run_command(command: Union[str, list[str]], cwd: str, log_output: bool = True, ignore_error: bool = False) -> str:
    if isinstance(command, str):
        cmd_text = command
        command = shlex.split(command)
    elif isinstance(command, list):
        cmd_text = " ".join(command)
    else:
        raise ValueError("command must be a string or list of strings")
    log.info(f"CMD: {cmd_text}")

    try:
        proc = subprocess.run(
            command, cwd=cwd, env=os.environ.copy(), capture_output=True, text=True, check=False, timeout=300
        )
        if proc.returncode == 0:
            if log_output:
                if proc.stdout:
                    log.info(f" STDOUT:\n{proc.stdout}")
                if proc.stderr:
                    log.info(f" STDERR:\n{proc.stderr}")
            return proc.stdout.strip()

        if ignore_error:
            return None

        log.error(f"Command failed: {cmd_text}")
        log.error(f" Exit: {proc.returncode}")
        log.error(f" STDOUT:\n{proc.stdout}")
        log.error(f" STDERR:\n{proc.stderr}")
        raise subprocess.CalledProcessError(proc.returncode, command, output=proc.stdout, stderr=proc.stderr)
    except subprocess.CalledProcessError as e:
        if ignore_error:
            return None
        log.error(f"Command failed: {cmd_text}")
        log.error(f" Exception: {e}")
        raise e


def ensure_pool_holder(pool: Pool) -> PoolHolder:
    with _pool_lock:
        prefix = f"{pool.id} ({pool.name}):"

        pool_holder = _pool_cache.get(pool.id)
        if pool_holder:
            just_created = False
        else:
            just_created = True
            pool_holder = PoolHolder(
                pool=pool,
                last_vars="",
                last_template="",
                pool_dir=os.path.join(os.getcwd(), ".lcm", pool.id),
                vms=None,
                vm_resource_type_name="",
            )
            _pool_cache[pool.id] = pool_holder

            os.makedirs(pool_holder.pool_dir, exist_ok=True)
            log.info(f"{prefix} pool state initialized at {pool_holder.pool_dir}")

        # Update terraform.tfvars if needed
        custom_vars = pool.customVariables
        if custom_vars and custom_vars != pool_holder.last_vars:
            pool_holder.last_vars = custom_vars
            tfvars_content = base64.b64decode(custom_vars).decode("utf-8")
            tfvars_path = os.path.join(pool_holder.pool_dir, "terraform.tfvars")
            log.info(f"{prefix} updating {tfvars_path}")
            with open(tfvars_path, "w") as f:
                f.write(tfvars_content)

        # Update main.tf if needed
        custom_template = pool.customTemplate
        if custom_template and custom_template != pool_holder.last_template:
            pool_holder.last_template = custom_template
            template_content = base64.b64decode(custom_template).decode("utf-8")
            template_path = os.path.join(pool_holder.pool_dir, "main.tf")
            log.info(f"{prefix} updating {template_path}")
            with open(template_path, "w") as f:
                f.write(template_content)

            # identify the VM resource type name from the template.
            # We require that the VM resource is named "vm" in the terraform template.
            # The pattern looks like below, 'resource "<type-name>" "vm" {'
            #    resource "proxmox_vm_qemu" "vm" {
            # or
            #    resource "proxmox_virtual_environment_vm" "vm" {
            # Scan each line to find the VM resource type
            vm_resource_type_name = None
            for line in template_content.splitlines():
                match = re.search(r'resource\s+"([^"]+)"\s+"vm"\s*\{', line)
                if match:
                    vm_resource_type_name = match.group(1)
                    log.info(f"{prefix} identified VM resource type: {vm_resource_type_name}")
                    break
            if not vm_resource_type_name:
                raise PluginException(f"{prefix} failed to identify Terraform VM resource type from custom template.")
            pool_holder.vm_resource_type_name = vm_resource_type_name

        if just_created:
            # Need to load from terraform, the existing vms
            auto_vars_file_path = os.path.join(pool_holder.pool_dir, "vms.auto.tfvars")
            vms_file = VmsAutoTfvarsFile(auto_vars_file_path)
            vms_file.hcs_group_id = "hcs-" + pool.id
            if vms_file.load():
                pool_holder.vms = vms_file.vms
                log.info(f"{prefix} loaded {len(pool_holder.vms)} VMs from previous vms.auto.tfvars")
            else:
                # No existing file, start fresh
                log.info(f"{prefix} starting fresh vms.auto.tfvars")
                pool_holder.vms = {}
                vms_file.vms = {}
                vms_file.write()
            # Ensure terraform is initialized with the plugin
            run_command("terraform init", cwd=pool_holder.pool_dir)
            run_command("terraform validate", cwd=pool_holder.pool_dir)
            refresh_all_vms_from_terraform_state(pool_holder)

        return pool_holder


def ensure_init_terraform():
    global _initialized
    if _initialized:
        return
    try:
        subprocess.run(["terraform", "version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log.error("Terraform executable is not available on PATH")
        return

    if "TF_PLUGIN_CACHE_DIR" not in os.environ:
        cache_dir = os.path.join(os.getcwd(), ".lcm", ".terraform-cache")
        log.info("TF_PLUGIN_CACHE_DIR is not set; using default cache directory: %s", cache_dir)
        os.makedirs(cache_dir, exist_ok=True)
        os.environ["TF_PLUGIN_CACHE_DIR"] = cache_dir
    _initialized = True


def terraform_apply(pool: Pool) -> None:
    pool_holder = ensure_pool_holder(pool)
    vms_auto_tfvars_file = VmsAutoTfvarsFile(os.path.join(pool_holder.pool_dir, "vms.auto.tfvars"))
    vms_auto_tfvars_file.hcs_group_id = "hcs-" + pool.id
    vms_auto_tfvars_file.vms = pool_holder.vms
    vms_auto_tfvars_file.write()
    log.info(f"{pool.id} ({pool.name}): #vms={len(pool_holder.vms)}")
    ensure_init_terraform()
    run_command("terraform apply -auto-approve", cwd=pool_holder.pool_dir)


def get_vm(pool: Pool, vmId: str, raise_on_not_found: bool = True) -> Optional[VmHolder]:
    pool_holder = ensure_pool_holder(pool)
    vm_holder = pool_holder.vms.get(vmId)
    if not vm_holder and raise_on_not_found:
        raise PluginException(f"VM {vmId} not found in pool {pool.id}")
    return vm_holder


def refresh_all_vms_from_terraform_state(pool_holder: PoolHolder) -> None:
    run_command("terraform refresh", cwd=pool_holder.pool_dir)
    stdout = run_command(
        f"terraform state list {pool_holder.vm_resource_type_name}.vm", cwd=pool_holder.pool_dir, ignore_error=True
    )
    if not stdout:
        return
    for line in stdout.splitlines():
        vm_id_match = re.match(rf"{pool_holder.vm_resource_type_name}\.vm\[(\"|')([^\"']+)(\"|')\]", line)
        if not vm_id_match:
            log.info(f"{pool_holder.pool.id} skipping unrecognized terraform state line: {line}")
            continue
        vm_id = vm_id_match.group(2)
        if not vm_id:
            continue
        refresh_vm_info(pool_holder.pool, vm_id)


def refresh_vm_info(pool: Pool, vmId: str, cloud_refresh: bool = False) -> Optional[VmInfo]:
    pool_holder = ensure_pool_holder(pool)
    try:
        if cloud_refresh:
            run_command(
                ["terraform", "refresh", "-target", f'{pool_holder.vm_resource_type_name}.vm["{vmId}"]'],
                cwd=pool_holder.pool_dir,
                ignore_error=True,
            )

        output = run_command(
            ["terraform", "state", "show", f'{pool_holder.vm_resource_type_name}.vm["{vmId}"]'],
            cwd=pool_holder.pool_dir,
            ignore_error=True,
        )
    except Exception:
        # already logged. Ignore
        pass

    if not output:
        log.info(f"{pool.id}/{vmId}: VM not found in terraform state")
        pool_holder.vms.pop(vmId, None)
        return None

    # we successfully refreshed the VM.
    vm_holder = pool_holder.vms.get(vmId)
    if not vm_holder:
        vm_holder = VmHolder(
            custom_data="", power_state="off", info=VmInfo(id=vmId, cloudId=None, powerState=PowerState.PoweredOff)
        )
        pool_holder.vms[vmId] = vm_holder

    for state_line in output.splitlines():
        state_line = state_line.strip()
        if not state_line:
            continue

        # identify cloud id
        #   id = "102"
        # or
        #   vm_id = 102
        cloud_id_match = re.match(r"id\s*=\s*(.+)", state_line)
        if not cloud_id_match:
            cloud_id_match = re.match(r"vm_id\s*=\s*(.+)", state_line)
        # strip quotes if any
        if cloud_id_match:
            vm_holder.info.cloudId = cloud_id_match.group(1).strip().strip('"').strip("'")

        # identify power state
        power_state_match = re.match(r"power_state\s*=\s*\"([^\"]+)\"", state_line)
        if not power_state_match:
            power_state_match = re.match(r"started\s*=\s*(.+)?\s*", state_line)
        if power_state_match:
            power_state = power_state_match.group(1).lower()
        else:
            power_state = "false"  # default to off
        if power_state in ["on", "running", "true", "1", "yes", "started", "poweredon", "powered_on"]:
            vm_holder.power_state = "on"
            vm_holder.info.powerState = PowerState.PoweredOn
        elif power_state in ["off", "stopped", "false", "0", "no", "stopped", "poweredoff", "powered_off"]:
            vm_holder.power_state = "off"
            vm_holder.info.powerState = PowerState.PoweredOff
        else:
            log.warning(f"{pool.id}/{vmId} unrecognized power state '{power_state}' from terraform state")
            vm_holder.power_state = "on"
            vm_holder.info.powerState = PowerState.Unknown
    log.info(f"{pool.id}/{vmId} refreshed: cloudId={vm_holder.info.cloudId}, powerState={vm_holder.info.powerState}")
    return vm_holder.info
