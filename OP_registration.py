import json
import os
import re
from datetime import datetime

import click
import dateutil.parser
import inquirer
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from playwright.sync_api import Playwright, expect, sync_playwright

email = os.getenv("GOTHAM_EMAIL")
password = os.getenv("GOTHAM_PASSWORD")
signature = os.getenv("GOTHAM_SIGNATURE")
url = "https://gothamvolleyball.leagueapps.com/events/4598263-division-8-11-power-e-g--w2-open-play-apr-28"
positions = [
    "Setter",
    "Outside",
    "Middle",
    "Opposite",
]


def run(playwright: Playwright) -> None:
    browser = playwright.firefox.launch(headless=False)
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    page.goto(url)

    page.wait_for_selector("iframe")
    framePage = page.frame_locator("#monolith-iframe")

    framePage.get_by_role("link", name="Register").click()
    framePage.locator("#reg-fa").click()
    page.wait_for_timeout(2000)
    page.get_by_role("link", name="Sign in with LeagueApps").click()

    page.get_by_role("textbox", name="Email").click()
    page.get_by_role("textbox", name="Email").fill(email)
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("button", name="Sign in with LeagueApps").click()
    framePage.locator('input[type="checkbox"][value="I am eligible"]').check()
    framePage.locator(f'input[type="checkbox"][value={positions[0]}]').check()

    framePage.get_by_text("Next", exact=True).click()

    framePage.locator('label[for="waiver-accept-cb-0"]').check()
    framePage.locator('label[for="waiver-accept-cb-1"]').check()
    framePage.locator('label[for="waiver-accept-cb-2"]').check()

    framePage.locator("#electronicSignature").click()
    framePage.locator("#electronicSignature").fill(signature)
    framePage.locator("#register-submit").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
