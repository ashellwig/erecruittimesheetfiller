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
"""Fills the Mon-Fri entries of an open eRecruit timesheet."""

import re
from dataclasses import dataclass
from datetime import datetime
from time import sleep

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from erecruittimesheetfiller.util.logger import setup_logger
from erecruittimesheetfiller.util.trace import dump_page_trace

# Each day has a widget with a unique id: `widget_day_<id>_<suffix>`.
START_INPUTS_XPATH = \
    "//input[starts-with(@id, 'widget_day_') and contains(@id, '_starttime')]"
START_SUFFIX = "_starttime"
END_SUFFIX = "_endtime"
BREAK_ADD_SUFFIX = "_btnBreakAdd"

# The lunch popup's inputs are readonly (picker only) and have generated ids.
LUNCH_INPUTS_XPATH = "//input[contains(@class, 'datetime-picker-time')]"

# The popup's Save looks exactly like the page's Save, so it is located
# relative to the lunch inputs (nearest ancestor that contains a Save).
POPUP_SAVE_XPATH = (
        "./ancestor::*[.//button[normalize-space(text())='Save']][1]"
        "//button[normalize-space(text())='Save']"
)

# The day's own green "Add" button that records the entry.
DAY_ADD_SUFFIX = "_btnsaveadd"


@dataclass(frozen=True)
class DayEntry:
    """Times to enter for a single day, in the format the portal expects."""

    start: str = "8:00 AM"
    end: str = "5:00 PM"
    lunch_start: str = "12:00 PM"
    lunch_end: str = "1:00 PM"


def _visible(driver: WebDriver, xpath: str) -> list[WebElement]:
    found = driver.find_elements(By.XPATH, xpath)
    return [e for e in found if e.is_displayed()]


def _click(element: WebElement) -> None:
    """Centres `element` and clicks it.

    The portal has fixed bars at the top (tabs) and bottom (Submit/Close)
    that cover elements scrolled to the viewport edge.
    """
    element.parent.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element
    )
    element.click()


def _type_time(field: WebElement, value: str) -> None:
    """Types a time into a normal (non-readonly) timepicker input."""
    _click(field)
    field.clear()
    field.send_keys(value)
    field.send_keys(Keys.TAB)  # Blur so the page's bindings pick it up.


def _set_readonly_time(driver: WebDriver, field: WebElement,
                       value: str) -> None:
    """Sets a readonly knockout-bound input, firing the events it listens to.

    The input only accepts picker clicks from a user, but its binding uses
    `valueUpdate: 'keyup'`, so setting the value and firing events works.
    """
    driver.execute_script(
            "arguments[0].value = arguments[1];"
            "for (const t of ['input', 'keyup', 'change'])"
            "  arguments[0].dispatchEvent(new Event(t, {bubbles: true}));",
            field,
            value,
    )


def _fill_lunch(driver: WebDriver, add_button: WebElement,
                entry: DayEntry) -> None:
    _click(add_button)
    WebDriverWait(driver, 10).until(
            lambda d: len(_visible(d, LUNCH_INPUTS_XPATH)) >= 2
    )
    lunch_start, lunch_end = _visible(driver, LUNCH_INPUTS_XPATH)[:2]
    _set_readonly_time(driver, lunch_start, entry.lunch_start)
    _set_readonly_time(driver, lunch_end, entry.lunch_end)
    popup_save = lunch_end.find_element(By.XPATH, POPUP_SAVE_XPATH)
    _click(popup_save)
    # Wait for the popup to close before touching the next day.
    WebDriverWait(driver, 10).until(EC.invisibility_of_element(popup_save))


def _reveal_day(driver: WebDriver, start_input: WebElement,
                prefix: str) -> None:
    """Clicks the day's add-time button if its time inputs are still hidden."""
    if start_input.is_displayed():
        return
    buttons = driver.find_elements(
            By.XPATH,
            f"//button[starts-with(@id, '{prefix}') "
            "and contains(@id, 'btnadd')]"
    )
    if not buttons:
        ids = driver.execute_script(
                "return [...document.querySelectorAll(arguments[0])]"
                ".map(e => e.tagName + '#' + e.id);",
                f"[id^='{prefix}']",
        )
        raise RuntimeError(f"Inputs hidden and no btnadd for {prefix}: {ids}")
    _click(buttons[0])
    WebDriverWait(driver, 10).until(lambda _: start_input.is_displayed())


def _confirm_day(driver: WebDriver, prefix: str) -> None:
    """Clicks the day's green "Add" and waits for the entry to collapse."""
    button = driver.find_element(By.ID, prefix + DAY_ADD_SUFFIX)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(button))
    _click(button)
    WebDriverWait(driver, 10).until(EC.invisibility_of_element(button))


def _existing_hours(driver: WebDriver, prefix: str) -> float:
    """Hours already recorded for the day, from its column's "N hours" text."""
    column = driver.find_element(
            By.XPATH, f"//*[@id='{prefix}_btnadd']/ancestor::td[1]"
    )
    match = re.search(r"(\d+(?:\.\d+)?)\s*hours", column.text)
    return float(match.group(1)) if match else 0.0


def _weekday_of(add_button: WebElement) -> int:
    """Weekday (Mon=0) from the add button's `date: 'MM/DD/YYYY'` tip args."""
    tip_args = add_button.get_attribute("data-tipargs") or ""
    match = re.search(r"date:\s*'(\d+/\d+/\d+)'", tip_args)
    if match is None:
        raise ValueError("Could not read the date from the break add button")
    return datetime.strptime(match.group(1), "%m/%d/%Y").weekday()


def fill_timesheet(
        driver: WebDriver,
        entry: DayEntry | None = None,
        dry_run: bool = True,
        expected_days: int = 7,
) -> None:
    """Enters `entry` for each Mon-Fri day of the timesheet currently open.

    The driver must already be switched into the `timesheet_manage_*` iframe
    (see `tools.login.automated`). With `dry_run` (the default) every field
    is filled but no day's "Add" is clicked, so nothing is recorded. The
    timesheet is never submitted either way. `expected_days` is how many day
    columns the timesheet has; filling waits until all of them are rendered.
    """
    logger = setup_logger(log_file="timesheet.log")
    entry = entry or DayEntry()

    # The day widgets render one by one; wait for all of them, or a slow
    # load leaves days out of the list below.
    try:
        WebDriverWait(driver, 15).until(
                lambda d: len(d.find_elements(By.XPATH, START_INPUTS_XPATH))
                >= expected_days
        )
    except TimeoutException as exc:
        driver.save_screenshot("timesheet_debug.png")
        add_buttons = driver.find_elements(
                By.XPATH, "//button[contains(@id, 'btnadd')]"
        )
        ids = driver.execute_script(
                "return [...document.querySelectorAll('[id*=\"widget_day\"]')]"
                ".slice(0, 30).map(e => e.tagName + '#' + e.id);"
        )
        found = len(driver.find_elements(By.XPATH, START_INPUTS_XPATH))
        logger.error("Only %d of %d day widgets. btnadd buttons: %d; "
                     "widget ids: %s",
                     found, expected_days, len(add_buttons), ids)
        raise RuntimeError(
                f"Only {found} of {expected_days} day inputs on the timesheet"
        ) from exc

    # Confirming a day can re-render the page, so collect the ids once and
    # look each day's elements up fresh.
    prefixes = [
            e.get_attribute("id")[:-len(START_SUFFIX)]
            for e in driver.find_elements(By.XPATH, START_INPUTS_XPATH)
    ]
    logger.debug("Found %d day widgets", len(prefixes))
    for prefix in prefixes:
        start_input = driver.find_element(By.ID, prefix + START_SUFFIX)
        end_input = driver.find_element(By.ID, prefix + END_SUFFIX)
        add_button = driver.find_element(By.ID, prefix + BREAK_ADD_SUFFIX)

        if _weekday_of(add_button) > 4:
            logger.debug("Skipping weekend widget %s", prefix)
            continue

        hours = _existing_hours(driver, prefix)
        if hours > 0:
            # Re-running must not add a second entry for the same day.
            logger.debug("Skipping %s: already has %s hours", prefix, hours)
            continue

        logger.debug("Filling %s: %s", prefix, entry)
        logger.debug("STEP %s: add time", prefix)
        _reveal_day(driver, start_input, prefix)
        logger.debug("STEP %s: start/end times", prefix)
        _type_time(start_input, entry.start)
        _type_time(end_input, entry.end)
        logger.debug("STEP %s: lunch", prefix)
        _fill_lunch(driver, add_button, entry)
        if dry_run:
            logger.debug("dry_run: not confirming %s", prefix)
        else:
            logger.debug("STEP %s: confirm day", prefix)
            _confirm_day(driver, prefix)
        sleep(1)
        dump_page_trace(driver, prefix)
