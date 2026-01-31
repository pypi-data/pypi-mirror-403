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
import hcs_core.sglib.cli_options as cli
import hcs_core.util.duration as duration
from hcs_core.ctxp import recent

import hcs_cli.service.admin as admin


@click.command(hidden=True)
@click.option(
    "--number",
    "-n",
    type=int,
    required=False,
    default=0,
    help="Number of VMs to expand. Use negative number to shrink.",
)
@click.option(
    "--to",
    "-t",
    type=int,
    required=False,
    default=0,
    help="Expected size of template.",
)
@click.argument("template_id", type=str, required=False)
@cli.org_id
@cli.wait
def expand(number: int, to: int, template_id: str, org: str, wait: str):
    """Update an existing template"""
    return expand_impl(number, to, template_id, org, wait, admin)


def expand_impl(number: int, to: int, template_id: str, org: str, wait: str, service):
    if to != 0 and number != 0:
        return "Specify either --to or --number, not both.", 1
    if to < 0:
        return "--to must be non-negative.", 1
    if to > 5000:
        return "--to exceeds maximum limit of 5000.", 1

    org_id = cli.get_org_id(org)

    template_id = recent.require("template", template_id)
    template = service.template.get(template_id, org_id)

    if not template:
        return "Template not found: " + template_id, 1

    spare_policy = template.get("sparePolicy", {})
    new_spare_policy = {
        "min": spare_policy.get("min", 0),
        "max": spare_policy.get("max", 0),
        "limit": spare_policy.get("limit", 0),
    }

    if to != 0:
        new_spare_policy["min"] = to
        new_spare_policy["max"] = to
        new_spare_policy["limit"] = to
    else:
        if number == 0:
            number = 1  # default to expand by 1
        new_spare_policy["min"] += number
        new_spare_policy["max"] += number
        new_spare_policy["limit"] += number

        if new_spare_policy["limit"] < 0:
            new_spare_policy["limit"] = 0
        elif new_spare_policy["limit"] > 5000:
            new_spare_policy["limit"] = 5000

        if new_spare_policy["min"] < 0:
            new_spare_policy["min"] = 0
        elif new_spare_policy["min"] > new_spare_policy["limit"]:
            new_spare_policy["min"] = new_spare_policy["limit"]
        if new_spare_policy["max"] < 0:
            new_spare_policy["max"] = 0
        elif new_spare_policy["max"] > new_spare_policy["limit"]:
            new_spare_policy["max"] = new_spare_policy["limit"]

    if (
        new_spare_policy["min"] == spare_policy.get("min", 0)
        and new_spare_policy["max"] == spare_policy.get("max", 0)
        and new_spare_policy["limit"] == spare_policy.get("limit", 0)
    ):
        # no change
        ret = template
    else:
        patch = {"sparePolicy": new_spare_policy}
        ret = service.template.patch(template_id, org_id, patch)

    if wait != "0":
        ret = service.template.wait_for_ready(template_id, org_id, duration.to_seconds(wait))
    return ret
