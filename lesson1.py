
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    page.goto("https://www.google.com/maps/search/?api=1&query=")

    input("Press Enter to close the browser...")

    browser.close()
