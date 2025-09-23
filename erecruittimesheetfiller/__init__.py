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
"""Global package variables for distribution."""

__all__ = (
        "__title__",
        "__summary__",
        "__uri__",
        "__version__",
        "__author__",
        "__email__",
        "__license__",
        "__copyright__",
)

__copyright__ = "Copyright (C) 2025 Ash Hellwig <ahellwig.dev@gmail.com>"

import email.utils
import importlib.metadata as importlib_metadata

metadata = importlib_metadata.metadata("erecruittimesheetfiller")

__title__ = metadata["name"]
__summary__ = metadata["summary"]
__uri__ = next(
        entry.split(", ")[1]
        for entry in metadata.get_all("Project-URL", ())
        if entry.startswith("Homepage")
)
__version__ = metadata["version"]
__author__, __email__ = email.utils.parseaddr(metadata["author-email"])
__license__ = "AGPL-3.0"
