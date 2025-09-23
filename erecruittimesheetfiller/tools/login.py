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
from selenium.webdriver.common.by import By

from erecruittimesheetfiller.util.logger import setup_logger


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
    logger = setup_logger(log_file="login.log")

    # Get the environment variables.
    logger.info("Loading environment variables...")
    load_dotenv()

    if os.getenv("ERECRUIT_LOGIN_URL") is not None:
        logger.debug("Environment variables loaded!")

    if login_url is None:
        login_url = os.getenv("ERECRUIT_LOGIN_URL")
    else:
        pass

    # Define webdriver.
    options = webdriver.ChromeOptions()
    drv = webdriver.Chrome(options=options)

    # Visit the sign in page.
    logger.debug("Visiting %s", login_url)

    drv.get(login_url)
    drv.set_window_size(615, 1012)

    # Log in to the site.
    logger.debug("Running login_to_erecruit now...")
    login_to_erecruit(driver=drv, username=username, password=password)

    # Close the browser.
    logger.debug("Closing the browser in 15 seconds.")
    sleep(15)
    logger.debug("Goodbye!")
    drv.quit()
