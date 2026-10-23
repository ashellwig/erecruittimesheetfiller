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
"""Yes/no dialog shown from a short-lived child process.

Tk can only take its windows off screen while its event loop runs. In the
main process that loop never runs while Selenium is working, so on macOS an
empty "tk" window stays up for the whole fill. A child process exits right
after the answer, and the OS removes its windows with it.

On macOS a background process's Tk window also opens behind other apps, so
there a native AppleScript dialog is used instead; `activate` brings it to
the front without needing any extra permissions.
"""

import subprocess
import sys

_TK_SCRIPT = """
import sys
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)
answer = messagebox.askyesno(sys.argv[1], sys.argv[2], parent=root)
root.destroy()
print("yes" if answer else "no")
"""

# Title and message arrive as `argv`, so no text is spliced into the script.
_APPLESCRIPT = [
        "on run argv",
        "activate",
        "set answer to button returned of (display dialog (item 2 of argv)"
        " with title (item 1 of argv) buttons {\"No\", \"Yes\"}"
        " default button \"Yes\" with icon note)",
        "return answer",
        "end run",
]


def ask_yes_no(title: str, message: str) -> bool:
    """Shows a yes/no dialog in front of other windows; True for "yes"."""
    if sys.platform == "darwin":
        command = ["osascript"]
        for line in _APPLESCRIPT:
            command += ["-e", line]
        command += [title, message]
    else:
        command = [sys.executable, "-c", _TK_SCRIPT, title, message]

    result = subprocess.run(
            command, capture_output=True, text=True, check=True
    )
    return result.stdout.strip().lower() == "yes"
