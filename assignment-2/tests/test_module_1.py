import pytest
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import json


@pytest.mark.asyncio
async def test_module():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            # timeout is in milliseconds — fail if the site doesn't respond in 15s
            await page.goto("https://www.bbc.com/news", timeout=15000)
        except PlaywrightTimeoutError:
            await browser.close()
            pytest.fail("Timed out trying to reach https://www.bbc.com/news")

        await page.wait_for_selector('[data-testid="card-headline"]', timeout=15000)
        data = await page.get_by_test_id("card-headline").all_inner_texts()

        try:
            first_five = data[:5]
        except Exception as e:
            print("Top 5 articles not available")

        json_data = {}
        for i in range(len(first_five)):
            json_data[f"article{i+1}"] = first_five[i]

        with open("top-articles.json", 'w') as f:
            json.dump(json_data, f, indent=4)
        await browser.close()
