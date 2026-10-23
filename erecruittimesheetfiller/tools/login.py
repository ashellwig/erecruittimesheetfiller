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
"""Signs into eRecruit site to begin our attempt to automate this process."""

import os

from time import sleep

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from erecruittimesheetfiller.tools.timesheet import fill_timesheet
from erecruittimesheetfiller.util.logger import setup_logger
from erecruittimesheetfiller.util.prompt import ask_yes_no
from erecruittimesheetfiller.util.trace import (
        dump_page_trace,
        install_page_trace,
        traced,
)


def login_to_erecruit(driver: WebDriver, username: str, password: str) -> None:

    # Username field.
    if username is None:
        username = os.getenv("ERECRUIT_USERNAME")
    else:
        pass

    username_field = driver.find_element(
            By.XPATH,
            "//*[@id=\"ctl00_cphMain_logIn_UserName\"]"
    )
    username_field.click()
    username_field.send_keys(username)

    # Password field.
    if password is None:
        password = os.getenv("ERECRUIT_PASSWORD")
    else:
        pass

    password_field = driver.find_element(
            By.XPATH,
            "//*[@id=\"ctl00_cphMain_logIn_Password\"]"
    )
    password_field.click()
    password_field.send_keys(password)

    # "Log In" button.
    login_button = driver.find_element(
            By.XPATH,
            "//*[@id=\"ctl00_cphMain_logIn_Login\"]"
    )
    login_button.click()


def automated(login_url: str, username: str, password: str) -> None:
    # Setup logger.
    logger = setup_logger(log_file="login.log")

    # Get the environment variables.
    logger.info("Loading environment variables...")
    load_dotenv()

    # Check if environment variables are available.
    if os.getenv("ERECRUIT_LOGIN_URL") is not None:
        logger.debug("Environment variables loaded!")

    # Retrieve log in URL.
    if login_url is None:
        login_url = os.getenv("ERECRUIT_LOGIN_URL")
    else:
        pass

    # Define webdriver.
    options = webdriver.ChromeOptions()
    # Every Selenium action is logged; see `util.trace`.
    drv = traced(webdriver.Chrome(options=options))

    # Visit the sign in page.
    logger.debug("Visiting %s", login_url)

    drv.get(login_url)
    drv.set_window_size(1366, 768)

    # Log in to the site.
    logger.debug("Running login_to_erecruit now...")
    login_to_erecruit(driver=drv, username=username, password=password)

    # Select the oldest time sheet available.
    # pylint: disable=C0301
    try:
        WebDriverWait(drv, 30).until(
                EC.frame_to_be_available_and_switch_to_it("dashboard")
        )
    except TimeoutException:
        logger.error(
                "Dashboard never loaded; still at %s. Check the login "
                "(bad credentials, MFA or a CAPTCHA?).",
                drv.current_url.split("?")[0]
        )
        drv.quit()
        raise
    tbody_xpath = "//*[@id=\"ctl00_cphMain_RadDock1455_C_ctl00_gridTimesheets_ctl00\"]/tbody"
    tbody_parent = drv.find_element(By.XPATH, tbody_xpath)
    tbody_rows = tbody_parent.find_elements(By.XPATH, "./*")

    # List available timesheets.
    for i in range(0, len(tbody_rows)):
        logger.debug("Count of available timesheets: %d", len(tbody_rows))
        logger.debug("-" * 50)
        payperiod_end_date = tbody_rows[i].find_elements(
                By.CLASS_NAME,
                "RadGridCellRightAlign"
        )[1].text
        logger.debug(
                "Row %d/%d: %s",
                i + 1,
                len(tbody_rows),
                payperiod_end_date
        )
        logger.debug("-" * 50)

        company = tbody_rows[i].find_element(By.TAG_NAME, "a").text

        # The only prompt: confirm which timesheet before anything is typed.
        # It runs in its own process so no Tk window lingers during the fill.
        edit_decision = ask_yes_no(
                f"Pay Period Ending {payperiod_end_date}",
                f"Fill this timesheet?\n\n{company}\n"
                f"Pay period ending {payperiod_end_date}\n\n"
                "Mon-Fri: 8:00 AM - 5:00 PM, lunch 12:00 PM - 1:00 PM\n"
                "Each day is added; the timesheet is NOT submitted."
        )

        if edit_decision:
            logger.debug(
                    "Now editing timesheet for pay period ending: %s",
                    payperiod_end_date
            )

            timesheet_link = tbody_rows[i].find_elements(By.XPATH, "./*")
            clicked_html = timesheet_link[0].get_attribute("outerHTML")
            # Click the <a> itself; the <td> is wider than the link.
            timesheet_link[0].find_element(By.TAG_NAME, "a").click()
            frame_xpath = "//iframe[starts-with(@id, 'timesheet_manage_')]"

            def find_timesheet_frame(driver: WebDriver, xpath=frame_xpath):
                """Looks at the top level, then inside the dashboard frame."""
                for in_dashboard in (False, True):
                    driver.switch_to.default_content()
                    if in_dashboard:
                        driver.switch_to.frame("dashboard")
                    found = driver.find_elements(By.XPATH, xpath)
                    if found:
                        return found[0]
                return False

            try:
                timesheet_frame = WebDriverWait(drv, 30).until(
                        find_timesheet_frame
                )
            except TimeoutException:
                drv.save_screenshot("timesheet_debug.png")
                logger.error("Clicked cell: %s", clicked_html)
                for in_dashboard in (False, True):
                    drv.switch_to.default_content()
                    if in_dashboard:
                        drv.switch_to.frame("dashboard")
                    logger.error(
                            "iframes (dashboard=%s): %s",
                            in_dashboard,
                            [f.get_attribute("id")
                             for f in drv.find_elements(By.TAG_NAME, "iframe")]
                    )
                raise
            drv.switch_to.frame(timesheet_frame)
            install_page_trace(drv)

            timesheet_tr_xpath = \
                "//*[@id=\"ctl00_ctl00_cphMain_cphMain_tblTimeDays\"]/tbody/tr"
            timesheet_tr = drv.find_element(By.XPATH, timesheet_tr_xpath)
            timesheet_days = timesheet_tr.find_elements(By.XPATH, "./*")
            logger.debug("-" * 50)
            logger.debug(
                    "Found %s elements under timesheet_tbody.",
                    len(timesheet_days)
            )
            logger.debug("-" * 50)

            # Fills and confirms ("Add") Mon-Fri. Submit is left to you.
            fill_timesheet(
                    drv, dry_run=False, expected_days=len(timesheet_days)
            )
            logger.debug("Days added; not submitted. Closing in 15 seconds.")
            sleep(15)
            dump_page_trace(drv, "review")

            # Close timesheet.
            # pylint: disable=C0301
            timesheet_close_button_xpath = \
                "//*[@id=\"ctl00_ctl00_cphMain_cphBottomButtons_btnCommonClose_input\"]"
            timesheet_close_button = drv.find_element(
                    By.XPATH,
                    timesheet_close_button_xpath
            )
            timesheet_close_button.click()
            sleep(3)
            drv.switch_to.default_content()
            drv.switch_to.frame("dashboard")
        else:
            pass

    drv.switch_to.default_content()

    # Close the browser.
    logger.debug("Closing the browser in 25 seconds.")
    sleep(3)
    logger.debug("Goodbye!")
    drv.quit()
