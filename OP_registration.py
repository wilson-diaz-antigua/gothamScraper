import json
import os
import re
from datetime import datetime

import dateutil.parser
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from playwright.sync_api import Playwright, expect, sync_playwright

email = os.getenv("GOTHAM_EMAIL")
password = os.getenv("GOTHAM_PASSWORD")
signature = os.getenv("GOTHAM_SIGNATURE")
url = "https://gothamvolleyball.leagueapps.com/events/4576309-division-3-7-power-b-d--w--open-play-apr-14"


def run(playwright: Playwright) -> None:
    browser = playwright.firefox.launch(headless=False)
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    page.goto(url)

    page.wait_for_selector("iframe")
    page.locator("#monolith-iframe").content_frame.get_by_role(
        "link", name="Register"
    ).click()
    page.locator("#monolith-iframe").content_frame.locator("#reg-fa").click()
    page.get_by_role("textbox", name="Email").click()
    page.get_by_role("textbox", name="Email").fill(email)
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("link", name="Sign in with LeagueApps").click()

    page.get_by_role("textbox", name="Email").click()
    page.get_by_role("textbox", name="Email").fill(email)
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("button", name="Sign in with LeagueApps").click()
    page.locator("#monolith-iframe").content_frame.locator(
        'input[name="prop_36646239"]'
    ).check()
    page.locator("#monolith-iframe").content_frame.get_by_role("checkbox").nth(
        3
    ).check()

    page.locator("#monolith-iframe").content_frame.get_by_text(
        "Next", exact=True
    ).click()
    page.locator("#monolith-iframe").content_frame.get_by_role(
        "tab", name=" I have read and accept the"
    ).locator("label").click()
    page.locator("#monolith-iframe").content_frame.get_by_role(
        "tab",
        name=" I have read and accept the Refund/Credit Policy terms and conditions",
    ).locator("label").click()
    page.locator("#monolith-iframe").content_frame.get_by_role(
        "tab",
        name=" I have read and accept the Photo and video release terms and conditions",
    ).locator("label").click()
    page.locator("#monolith-iframe").content_frame.locator(
        "#electronicSignature"
    ).click()
    page.locator("#monolith-iframe").content_frame.locator("#electronicSignature").fill(
        signature
    )
    page.locator("#monolith-iframe").content_frame.locator("#register-submit").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
