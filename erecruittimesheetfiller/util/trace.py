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
"""Debug tracing: logs Selenium actions and in-page clicks/inputs/dialogs."""

import logging

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.events import (
        AbstractEventListener,
        EventFiringWebDriver,
)

# Same logger as `util.logger.setup_logger`, so traces land in its log file.
_logger = logging.getLogger("erecruittimesheetfiller.util.logger")


def _describe(element: WebElement) -> str:
    try:
        tag = element.tag_name
        el_id = element.get_attribute("id") or ""
        text = (element.text or "").strip()[:30]
        return f"<{tag} id={el_id!r} text={text!r}>"
    except Exception:  # pylint: disable=W0718
        return "<stale element>"


class _ActionLogger(AbstractEventListener):
    """Logs every click and keystroke Selenium sends, with a timestamp."""

    def before_click(self, element, driver):
        _logger.debug("SELENIUM click %s", _describe(element))

    def before_change_value_of(self, element, driver):
        # Values are not logged so a password field is never written out.
        _logger.debug("SELENIUM send_keys/clear %s", _describe(element))

    def after_navigate_to(self, url, driver):
        _logger.debug("SELENIUM navigated to %s", url.split("?")[0])

    def on_exception(self, exception, driver):
        _logger.debug("SELENIUM exception %s", type(exception).__name__)


def traced(driver: WebDriver) -> EventFiringWebDriver:
    """Wraps `driver` so every Selenium action is logged."""
    return EventFiringWebDriver(driver, _ActionLogger())


# Records clicks, changes and JS dialogs in the current frame. Capture-phase
# listeners see events even if the page stops them. Password fields are
# never recorded.
_INSTALL_JS = """
if (window.__ertfTrace) { return; }
window.__ertfTrace = [];
const log = (kind, detail) => window.__ertfTrace.push(
    new Date().toISOString().slice(11, 23) + ' ' + kind + ' ' + detail);
const describe = (el) => {
    if (!el || !el.tagName) { return String(el); }
    const text = (el.innerText || el.value || '').trim().slice(0, 30);
    return '<' + el.tagName.toLowerCase() + ' id=' + JSON.stringify(el.id)
        + ' class=' + JSON.stringify(el.className || '')
        + ' text=' + JSON.stringify(text) + '>';
};
for (const type of ['click', 'change']) {
    document.addEventListener(type, (e) => {
        if (e.target && e.target.type === 'password') { return; }
        log(e.isTrusted ? 'USER ' + type : 'SCRIPT ' + type, describe(e.target));
    }, true);
}
for (const name of ['alert', 'confirm', 'prompt']) {
    const original = window[name];
    window[name] = function (...args) {
        log('DIALOG ' + name, JSON.stringify(String(args[0]).slice(0, 200)));
        const result = original.apply(window, args);
        log('DIALOG ' + name + ' result', JSON.stringify(result));
        return result;
    };
}
window.addEventListener('beforeunload', () => log('PAGE', 'beforeunload'));
"""


def install_page_trace(driver: WebDriver) -> None:
    """Starts recording in the frame the driver is currently switched to."""
    driver.execute_script(_INSTALL_JS)


def dump_page_trace(driver: WebDriver, label: str) -> None:
    """Logs and clears what the page recorded since the last dump."""
    entries = driver.execute_script(
            "const t = window.__ertfTrace || []; window.__ertfTrace = [];"
            "return t;"
    )
    for entry in entries:
        _logger.debug("PAGE[%s] %s", label, entry)
