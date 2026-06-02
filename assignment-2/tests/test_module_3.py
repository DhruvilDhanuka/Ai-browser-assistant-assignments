import json
from playwright.async_api import async_playwright
import pytest
import asyncio


async def test_module_3():

    async def open_tab(browser, url):
        try:
            page = await browser.new_page()
            await page.goto(url, timeout=10000)
            return await page.title()
        except Exception as e:
            raise Exception(f"Could not load the {url} due to {e}")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        browser = await browser.new_context()

        urls = ["https://www.youtube.com", "https://www.discord.com",
                "https://www.linkedin.com", "https://www.instagram.com", "https://www.facebook.com"]

        result = await asyncio.gather(*(open_tab(browser, u) for u in urls), return_exceptions=True)

        print("GOT RESULTS=========================", result)
        # we will store the title in json files
        dict_result = {}

        for i in range(len(result)):
            if type(result[i]) == str:
                dict_result[f"page{i}_title"] = result[i]
            else:
                dict_result[f"page{i}_title"] = "COULD NOT FETCH "

        with open("page_titles_captured.json", 'w') as f:
            json.dump(dict_result, f, indent=4)
