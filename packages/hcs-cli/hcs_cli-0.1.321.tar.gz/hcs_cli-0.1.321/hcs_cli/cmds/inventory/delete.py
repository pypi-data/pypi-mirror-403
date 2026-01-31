"""
Copyright 2023-2023 VMware Inc.
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import click
from hcs_core.ctxp import recent
import hcs_core.sglib.cli_options as cli

from hcs_cli.service import inventory
from hcs_cli.support.param_util import parse_vm_path


@click.command()
@cli.org_id
@click.argument("vm_path", type=str, required=False)
def delete(org: str, vm_path: str):
    """Delete a VM by path, e.g., template1/vm1, or 'vm1,vm2,vm3'."""

    org_id = cli.get_org_id(org)

    if vm_path.find(",") > 0:
        vm_ids = [v.strip() for v in vm_path.split(",")]
        template_id = recent.require("template", None)
    else:
        template_id, vm_id = parse_vm_path(vm_path)
        ret = inventory.get(template_id, vm_id, org_id)
        if not ret:
            return "", 1
        vm_ids = [vm_id]

    ret = {"_requested_ids": vm_ids, "_accepted_ids": [], "_deleted": 0}
    vms = inventory.begin_deleting_vms_by_id(template_id, org_id, vm_ids)
    for vm in vms:
        ret["_accepted_ids"].append(vm["id"])
    actual_deleted = inventory.finish_deleting_vms(template_id, org_id, vm_ids)
    ret["_deleted"] = actual_deleted
    return ret
