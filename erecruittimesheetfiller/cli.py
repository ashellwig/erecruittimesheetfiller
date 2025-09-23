# Copyright (C) 2025 Ash Hellwig <ahellwig.dev@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Collects the CLI tools from each module and adds them to the main package."""

import importlib.metadata

import click

from erecruittimesheetfiller.tools.cli import cli_automated_login

ERTF_VERSION: str = importlib.metadata.version("erecruittimesheetfiller")


@click.group()
@click.version_option(
        version=ERTF_VERSION,
        package_name="erecruittimesheetfiller"
)
@click.pass_context
def cli(ctx):  # pylint: disable=W0613
    pass


cli.add_command(cli_automated_login, name="auto-login")

if __name__ == "__main__":
    cli()  # pylint: disable=E1120
