import pytest
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from pages.module_2_page import module_2_page
import json


def get_json_data():

    with open("./dummy_data.json", 'r') as f:
        data = json.load(f)

    # parametrize wants a list of test cases; each case is a tuple of the 14 field values.
    # One record -> a list with a single tuple.
    return [tuple(data.values())]


@pytest.mark.parametrize(
    "first_name,last_name,email_address,gender,phone_number,day,month,year,subjects,hobbies,picture_path,curr_adress,state,city", get_json_data())
async def test_module2(first_name, last_name, email_address, gender, phone_number, day, month, year, subjects, hobbies, picture_path, curr_adress, state, city):

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=400, timeout=12000)
        browser = await browser.new_context()
        page = await browser.new_page()
        await page.goto("https://demoqa.com/automation-practice-form", timeout=12000)

        form_fill = module_2_page(page)

        await form_fill.fill_name(first_name, last_name)
        await form_fill.fill_email(email_address)
        await form_fill.fill_gender(gender)
        await form_fill.fill_phone_number(phone_number)
        await form_fill.fill_DOB(day, month, year)
        await form_fill.fill_subjects(subjects)
        await form_fill.fill_hobbies(hobbies)
        await form_fill.fill_pictures_input(picture_path)
        await form_fill.fill_currAdress(curr_adress)
        await form_fill.fill_state_city(state, city)
        await form_fill.click_submit_button()
