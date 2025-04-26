#!/usr/bin/env python3
import json
import logging
import os
import re
import time
from datetime import datetime

import dateutil.parser
import schedule
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from playwright.sync_api import sync_playwright

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Generate a timestamped log file name
log_filename = datetime.now().strftime("logs/log_%Y-%m-%d_%H-%M-%S.log")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Could also use INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(),  # Print logs to console
    ],
)


def extract_event_details(li, context):
    """Extract event details from a list item."""
    scraped_event = {}
    a_tag = li.find("a", href=True)
    if a_tag:
        scraped_event["link"] = (
            f"https://gothamvolleyball.leagueapps.com{a_tag['href']}"
        )
        scraped_event["title"] = a_tag.get_text(strip=True)

    dd_tag = li.find("dd", class_="program-list-starts")
    if dd_tag:
        scraped_event["start_date"] = (
            dd_tag.get_text(strip=True).replace("\u00a0", " ").replace("\u2019", "'")
        )

    dd_tag = li.find("dd", class_="program-list-location")
    if dd_tag:
        location_a_tag = dd_tag.find("a", href=True)
        if location_a_tag:
            scraped_event["location"] = location_a_tag.get_text(strip=True)
            scraped_event["location_link"] = (
                f"https://gothamvolleyball.leagueapps.com{location_a_tag['href']}"
            )
        extract_schedule_details(scraped_event, context)

    return scraped_event


def extract_schedule_details(scraped_event, context):
    """Navigate to the event page and extract schedule details."""
    event_page = context.new_page()
    event_page.goto(scraped_event["link"])
    event_page.wait_for_selector("iframe")
    iframe_tag = event_page.query_selector("iframe").get_attribute("src")

    event_page.goto(f"https://gothamvolleyball.leagueapps.com{iframe_tag}")
    event_page.wait_for_selector("div.base-schedule")
    event_soup = BeautifulSoup(
        event_page.inner_html("div.base-schedule"), "html.parser"
    )

    em_tag = event_soup.find("em")
    if em_tag:
        time_range = em_tag.get_text(strip=True).split(" to ")
        scraped_event["start_time"] = time_range[0]
        scraped_event["end_time"] = time_range[1]
    else:
        scraped_event["time"] = "time not found"


def create_calendar_event(scraped_event):
    """Create a calendar event from scraped event details."""
    calendar_event = Event()
    calendar_event.add("summary", scraped_event.get("title", "Gotham Volleyball Event"))

    if "start_date" in scraped_event:
        try:
            start_date = dateutil.parser.parse(
                f'{scraped_event["start_date"]} {scraped_event["start_time"]}'
            )
            end_date = dateutil.parser.parse(
                f'{scraped_event["start_date"]} {scraped_event["end_time"]}'
            )
            calendar_event.add("dtstart", start_date)
            calendar_event.add("dtend", end_date)
        except:
            calendar_event.add("dtstart", datetime(2025, 4, 20, 10, 0, 0))
    else:
        calendar_event.add("dtstart", datetime(2025, 4, 20, 10, 0, 0))

    if "link" in scraped_event:
        calendar_event.add("url", scraped_event["link"])
    if "location" in scraped_event:
        calendar_event.add("location", scraped_event["location"])
    if "location_link" in scraped_event:
        calendar_event.add(
            "description", f"Location link: {scraped_event['location_link']}"
        )

    return calendar_event


def main():
    cal = Calendar()
    scraped_events_list = []

    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        )
        page = context.new_page()
        page.goto(
            "https://gothamvolleyball.leagueapps.com/events/4470169-mixed-open-plays-spring-2025?ngmp_2023_iframe_transition=1"
        )
        page.wait_for_selector("div.base-listing--subprogram")
        soup = BeautifulSoup(
            page.inner_html("div.base-listing--subprogram"), "html.parser"
        )

        for li in soup.find_all("li", id=re.compile(r"^baseevent-")):
            scraped_event = extract_event_details(li, context)
            if scraped_event:
                calendar_event = create_calendar_event(scraped_event)
                cal.add_component(calendar_event)
                scraped_events_list.append(scraped_event)

    with open("events.json", "w") as json_file:
        json.dump(scraped_events_list, json_file, indent=4)

    with open("my_calendar.ics", "wb") as f:
        f.write(cal.to_ical())


def test():
    return "Test function executed successfully!"


def check_calendar_diff():
    """Check for differences in the calendar file before and after running main()."""
    try:
        with open("my_calendar.ics", "rb") as f:
            old_calendar = f.read()
    except FileNotFoundError:
        logging.warning("my_calendar.ics not found, assuming no prior calendar.")
        old_calendar = b""

    main()  # Trigger the main function to update the calendar

    with open("my_calendar.ics", "rb") as f:
        new_calendar = f.read()

    if old_calendar != new_calendar:
        logging.info("Calendar has been updated with new events.")

    else:
        logging.info("No changes detected in the cal1endar.")


schedule.every().day.at("11:30").do(check_calendar_diff)
while True:
    logging.info("schedule running... ")
    schedule.run_pending()
    time.sleep(30 * 60)  # Sleep for 30 minutes
