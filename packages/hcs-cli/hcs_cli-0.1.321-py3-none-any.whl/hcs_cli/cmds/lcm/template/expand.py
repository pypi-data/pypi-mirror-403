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

import hcs_cli.service.lcm as lcm
from hcs_cli.cmds.template.expand import expand_impl


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

    return expand_impl(number, to, template_id, org, wait, lcm)
