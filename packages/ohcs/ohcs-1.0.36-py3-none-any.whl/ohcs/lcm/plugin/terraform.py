# ----------------------------------------------------------------------------
# Copyright (c) Omnissa, LLC. All rights reserved.
# This product is protected by copyright and intellectual property laws in the
# United States and other countries as well as by international treaties.
# ----------------------------------------------------------------------------

from datetime import datetime
from typing import Any, Optional, Union

from ohcs.lcm.api import Pool, VmInfo, PowerState
import logging
from . import tf_helper

log = logging.getLogger(__name__)


def init() -> Optional[dict[str, Any]]:
    log.info("Terraform plugin initialized")
    return None


def health(pool: Pool, params: dict[str, Any]) -> dict[str, Any]:
    ret: dict[str, Union[str, int]] = {"date": datetime.now().isoformat()}

    try:
        tf_helper.ensure_init_terraform()
        pool_holder = tf_helper.ensure_pool_holder(pool)
        ret["vms"] = len(pool_holder.vms)
        ret["status"] = "Healthy"
    except Exception as e:
        ret["status"] = "Unhealthy"
        ret["error"] = str(e)

    return ret


def prepare_pool(pool: Pool, params: dict[str, Any]) -> Optional[dict[str, Any]]:
    tf_helper.ensure_pool_holder(pool)
    return None


def destroy_pool(pool: Pool, params: dict[str, Any]) -> None:
    pool_holder = tf_helper.ensure_pool_holder(pool)

    # clear all VMs
    pool_holder.vms.clear()
    tf_helper.terraform_apply(pool)

    # destroy everything
    tf_helper.run_command("terraform apply -destroy -auto-approve", cwd=pool_holder.pool_dir)


def list_vms(pool: Pool, params: dict[str, Any]) -> list[VmInfo]:
    pool_holder = tf_helper.ensure_pool_holder(pool)
    tf_helper.refresh_all_vms_from_terraform_state(pool_holder)
    ret: list[VmInfo] = []
    for vm_id in pool_holder.vms.keys():
        vm_info = pool_holder.vms[vm_id].info
        ret.append(vm_info)
    return ret


def get_vm(pool: Pool, vmId: str) -> Optional[VmInfo]:
    if not vmId:
        log.warning(f"{pool.id} get_vm called with empty vmId")
        return None
    return tf_helper.refresh_vm_info(pool, vmId, cloud_refresh=True)


def create_vm(pool: Pool, vmId: str, params: dict[str, Any]) -> VmInfo:
    pool_holder = tf_helper.ensure_pool_holder(pool)
    vm_spec = params.get("vmSpec", "")
    vm_holder = tf_helper.VmHolder(
        custom_data=vm_spec, power_state="on", info=VmInfo(id=vmId, cloudId=None, powerState=PowerState.PoweredOn)
    )
    pool_holder.vms[vmId] = vm_holder
    tf_helper.terraform_apply(pool)
    return tf_helper.refresh_vm_info(pool, vmId)


def delete_vm(pool: Pool, vmId: str, params: dict[str, Any]) -> None:
    pool_holder = tf_helper.ensure_pool_holder(pool)
    vm_holder = pool_holder.vms.get(vmId)
    if not vm_holder:
        return
    del pool_holder.vms[vmId]
    tf_helper.terraform_apply(pool)


def power_on_vm(pool: Pool, vmId: str, params: dict[str, Any]) -> VmInfo:
    vm_holder = tf_helper.get_vm(pool, vmId)
    vm_holder.power_state = "on"
    tf_helper.terraform_apply(pool)
    return tf_helper.refresh_vm_info(pool, vmId)


def power_off_vm(pool: Pool, vmId: str, params: dict[str, Any]) -> VmInfo:
    vm_holder = tf_helper.get_vm(pool, vmId)
    vm_holder.power_state = "off"
    tf_helper.terraform_apply(pool)
    return tf_helper.refresh_vm_info(pool, vmId)


def shutdown_vm(pool: Pool, vmId: str, params: dict[str, Any]) -> VmInfo:
    vm_holder = tf_helper.get_vm(pool, vmId)
    try:
        vm_holder.power_state = "shutdown"
        tf_helper.terraform_apply(pool)
    except Exception as e:
        log.warning(f"Failed to shutdown VM {pool.id}/{vmId}: {e}. Forcing power off.")
        vm_holder.power_state = "off"
        tf_helper.terraform_apply(pool)
    return tf_helper.refresh_vm_info(pool, vmId)


# -------------------- Unsupported optional functions --------------------

# def restart_vm(pool: Pool, vmId: str, params: dict[str, Any]) -> VmInfo:
#     raise NotImplementedError("restart_vm is not supported by this plugin")


# def hibernate_vm(pool: Pool, vmId: str, params: dict[str, Any]) -> VmInfo:
#     raise NotImplementedError("hibernate_vm is not supported by this plugin")


# def snapshot_vm(pool: Pool, vmId: str, params: dict[str, Any]) -> VmInfo:
#     raise NotImplementedError("snapshot_vm is not supported by this plugin")


# def restore_vm(pool: Pool, vmId: str, params: dict[str, Any]) -> VmInfo:
#     raise NotImplementedError("restore_vm is not supported by this plugin")


# def resize_vm(pool: Pool, vmId: str, params: dict[str, Any]) -> VmInfo:
#     raise NotImplementedError("resize_vm is not supported by this plugin")
