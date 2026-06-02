import pytest
from playwright.async_api import async_playwright
from calendar import month_name as cal_month
import re


class module_2_page():

    def __init__(self, page):

        self.page = page
        self.first_name_input = page.get_by_role(
            "textbox", name="First Name")

        self.last_name_input = page.get_by_role(
            "textbox", name="Last Name")

        self.email_input = page.get_by_role(
            "textbox", name="name@example.com")

        self.mobile_number_input = page.get_by_role(
            "textbox", name="Mobile Number")

        self.current_address_input = page.get_by_role(
            "textbox", name="Current Address")

        # For gender radio buttons we will use regex and then select the one which is choosen by the user during the call of function only
        # same we can do for hobbies

        self.picture_input = page.locator("#uploadPicture")

        self.state_input = page.locator(
            "#state > .css-13cymwt-control > .css-1wy0on6 > .css-1xc3v61-indicatorContainer > .css-8mmkcg")

        self.city_input = page.locator(
            "#city > .css-13cymwt-control > .css-1wy0on6 > .css-1xc3v61-indicatorContainer > .css-8mmkcg")

        self.submit_button = page.get_by_role("button", name="Submit")

        self.dob_locator = page.locator("#dateOfBirthInput")

        self.subjects_input = page.locator(
            ".subjects-auto-complete__input-container")

    async def fill_name(self, first_name, last_name):
        await self.first_name_input.fill(first_name)
        await self.last_name_input.fill(last_name)

    async def fill_email(self, email_address):
        await self.email_input.fill(email_address)

    async def fill_gender(self, gender):
        # Match the radio's accessible name case-insensitively so "male"/"MALE"/"Male" all work.
        # ^...$ anchors keep it exact (so "Male" doesn't also match a hypothetical "Male Other").
        pattern = re.compile(rf"^{re.escape(gender.strip())}$", re.IGNORECASE)
        try:
            await self.page.get_by_role("radio", name=pattern).check()
        except Exception:
            raise ValueError(
                f"Invalid gender '{gender}'. Expected one of: Male, Female, Other.")

    async def fill_phone_number(self, phone_number):
        await self.mobile_number_input.fill(phone_number)

    async def fill_subjects(self, subjects_arr):
        for subject in subjects_arr:
            await self.subjects_input.click()
            await self.subjects_input.type(subject)
            await self.page.wait_for_selector(".subjects-auto-complete__option")
            await self.subjects_input.press("Enter")

    async def fill_hobbies(self, hobbies):

        for hobby in hobbies:
            # Same case-insensitive, anchored match as gender so "sports" maps to "Sports".
            pattern = re.compile(
                rf"^{re.escape(hobby.strip())}$", re.IGNORECASE)
            try:
                await self.page.get_by_role("checkbox", name=pattern).check()
            except Exception:
                raise ValueError(
                    f"Invalid hobby '{hobby}'. Expected one of: Sports, Reading, Music.")

    async def fill_currAdress(self, curr_adress):
        await self.current_address_input.fill(curr_adress)

    async def fill_state_city(self, state, city):
        # Same case-insensitive, anchored matching as gender/hobbies.
        state_pattern = re.compile(
            rf"^{re.escape(state.strip())}$", re.IGNORECASE)
        await self.state_input.click()
        try:
            await self.page.get_by_role("option", name=state_pattern).click()
        except Exception:
            raise ValueError(
                f"Invalid state '{state}'. No such option in the dropdown.")

        city_pattern = re.compile(
            rf"^{re.escape(city.strip())}$", re.IGNORECASE)
        await self.city_input.click()
        try:
            await self.page.get_by_role("option", name=city_pattern).click()
        except Exception:
            raise ValueError(
                f"Invalid city '{city}'. No such option in the dropdown.")

    async def fill_pictures_input(self, picture_path):
        await self.picture_input.set_input_files(picture_path)

    async def fill_DOB(self, day, month, year):

        await self.dob_locator.click()
        month_number = list(cal_month).index(month) - 1
        await self.page.locator(
            ".react-datepicker__month-select").select_option(str(month_number))
        await self.page.locator(
            ".react-datepicker__year-select").select_option(str(year))
        await self.page.get_by_role("gridcell", name=re.compile(f"{month} {day}")).click()

    async def click_submit_button(self):
        await self.page.screenshot(path="screenshot.png")
        await self.submit_button.click()
