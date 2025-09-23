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

# eRecruit login URL.
$env:ERECRUIT_LOGIN_URL = "https://portal.insightglobal.com/Login.aspx"

# eRecruit username.
$env:ERECRUIT_USERNAME = "hellwigashton@gmail.com"

# eRecruit password.
$env:ERECRUIT_PASSWORD = "aaSShh52865!"

erecruittimesheetfiller auto-login `
    --login-url "$env:ERECRUIT_LOGIN_URL" `
    --username "$env:ERECRUIT_USERNAME" `
    --password "$env:ERECRUIT_PASSWORD"
