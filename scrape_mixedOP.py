import json
import re
from datetime import datetime

import dateutil.parser
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from playwright.sync_api import Playwright, expect, sync_playwright

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
    soup = BeautifulSoup(page.inner_html("div.base-listing--subprogram"), "html.parser")

    for li in soup.find_all("li", id=re.compile(r"^baseevent-")):
        scraped_event = {}
        # Extract the a tag with href and text
        a_tag = li.find("a", href=True)
        if a_tag:
            scraped_event["link"] = (
                f"https://gothamvolleyball.leagueapps.com{a_tag['href']}"
            )
            scraped_event["title"] = a_tag.get_text(strip=True)

        # Extract the dt tag with class "program-list-starts"
        dd_tag = li.find("dd", class_="program-list-starts")
        if dd_tag:
            scraped_event["start_time"] = (
                dd_tag.get_text(strip=True)
                .replace("\u00a0", " ")
                .replace("\u2019", "'")
            )

        # Extract the a tag inside dd tag with class "program-list-location"
        dd_tag = li.find("dd", class_="program-list-location")
        if dd_tag:
            location_a_tag = dd_tag.find("a", href=True)
            if location_a_tag:
                scraped_event["location"] = location_a_tag.get_text(strip=True)
                scraped_event["location_link"] = (
                    f"https://gothamvolleyball.leagueapps.com{location_a_tag['href']}"
                )

        if scraped_event:
            # Create a new Event object for each scraped event
            calendar_event = Event()

            # Add properties to the event
            calendar_event.add(
                "summary", scraped_event.get("title", "Gotham Volleyball Event")
            )

            # Parse the start_time if available
            if "start_time" in scraped_event:
                try:
                    # Try to parse the date from the start_time string
                    start_date = dateutil.parser.parse(scraped_event["start_time"])
                    calendar_event.add("dtstart", start_date)
                except:
                    # Fallback to default date if parsing fails
                    calendar_event.add("dtstart", datetime(2025, 4, 20, 10, 0, 0))
            else:
                calendar_event.add("dtstart", datetime(2025, 4, 20, 10, 0, 0))

            # Add other event details if available
            if "link" in scraped_event:
                calendar_event.add("url", scraped_event["link"])
            if "location" in scraped_event:
                calendar_event.add("location", scraped_event["location"])
            if "location_link" in scraped_event:
                calendar_event.add(
                    "description", f"Location link: {scraped_event['location_link']}"
                )

            # Add the event to the calendar
            cal.add_component(calendar_event)

            scraped_events_list.append(scraped_event)

    # Move this outside the loop to write all events at once
    with open("events.json", "w") as json_file:
        json.dump(scraped_events_list, json_file, indent=4)

with open("my_calendar.ics", "wb") as f:
    f.write(cal.to_ical())
