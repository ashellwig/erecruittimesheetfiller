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
"""Collects the functions of the `erecruittimesheetfiller.tools` module to make
usable by the click library for CLI use.
"""

import click

from erecruittimesheetfiller.tools.login import automated


@click.command()
@click.option("--login-url", envvar=["ERECRUIT_LOGIN_URL"])
@click.option("--username", envvar=["ERECRUIT_USERNAME"])
@click.option("--password", envvar=["ERECRUIT_PASSWORD"])
def cli_automated_login(login_url: str, username: str, password: str):
    automated(login_url=login_url, username=username, password=password)
