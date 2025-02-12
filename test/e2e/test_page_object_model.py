import pytest
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from test.e2e.utils import run_server, driver


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.popup_message = driver.find_element(By.ID, "pop-message")
    
    def assert_url_path(self, path: str):
        WebDriverWait(driver, timeout=2).until(lambda _: self.driver.current_url == f"http://localhost:8080/{path}")
    
    def assert_popup_message(self, message: str):
        WebDriverWait(driver, timeout=2).until(lambda _: self.popup_message.value_of_css_property('visibility') == "visible")
        assert self.popup_message.get_attribute('innerHTML') == message
        WebDriverWait(driver, timeout=5).until(lambda _: self.popup_message.value_of_css_property('visibility') == "hidden")


class WelcomePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.assert_url_path("")
        self.login_email = driver.find_element("id", "input-login-email")
        self.login_password = driver.find_element("id", "input-login-password")
        self.login_button = driver.find_element("id", "button-login")
        self.register_button = driver.find_element(By.ID, "button-register-window")
        self.firstname_input = driver.find_element(By.ID, "input-sign-up-first-name")
        self.lastname_input = driver.find_element(By.ID, "input-sign-up-last-name")
        self.gender_select = driver.find_element(By.ID, "input-sign-up-gender")
        self.city_input = driver.find_element(By.ID, "input-sign-up-city")
        self.country_input = driver.find_element(By.ID, "input-sign-up-country")
        self.email_input = driver.find_element(By.ID, "input-sign-up-email")
        self.password_input = driver.find_element(By.ID, "input-sign-up-password")
        self.password_repeat_input = driver.find_element(By.ID, "input-sign-up-password-repeat")
        self.submit_button = driver.find_element(By.ID, "button-register")

    def open_registration(self):
        self.register_button.click()
    
    def login(self, email: str, password: str):
        self.login_email.clear()
        self.login_email.send_keys(email)
        self.login_password.clear()
        self.login_password.send_keys(password)
        self.login_button.click()

    def register_user(self, firstname: str, lastname: str, gender: str, city: str, country: str, email: str, password: str):
        self.firstname_input.clear()
        self.firstname_input.send_keys(firstname)
        self.lastname_input.clear()
        self.lastname_input.send_keys(lastname)
        if gender_sel := Select(self.gender_select):
            gender_sel.select_by_visible_text(gender)
        self.city_input.clear()
        self.city_input.send_keys(city)
        self.country_input.clear()
        self.country_input.send_keys(country)
        self.email_input.clear()
        self.email_input.send_keys(email)
        self.password_input.clear()
        self.password_input.send_keys(password)
        self.password_repeat_input.clear()
        self.password_repeat_input.send_keys(password)
        self.submit_button.click()


class HomePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.assert_url_path("home")
        self.user_name = driver.find_element(By.ID, "home-user-name")
        self.user_gender = driver.find_element(By.ID, "home-user-gender")
        self.user_email = driver.find_element(By.ID, "home-user-email")
        self.user_location = driver.find_element(By.ID, "home-user-location")
        self.new_post_input = driver.find_element(By.ID, "input-home-new-post")
        self.new_post_button = driver.find_element(By.ID, "button-home-new-post")

    def verify_user_info(self, firstname, lastname, gender, city, country, email):
        assert self.user_name.text == f"{firstname} {lastname}"
        assert self.user_gender.text == gender
        assert self.user_email.text == email
        assert self.user_location.text == f"{city}, {country}"

    def add_post(self, content):
        self.new_post_input.clear()
        self.new_post_input.send_keys(content)
        self.new_post_button.click()


@pytest.mark.timeout(15)
def test_register_user(driver):
    driver.get("http://localhost:8080/")

    welcome_page = WelcomePage(driver)
    welcome_page.open_registration()
    welcome_page.register_user("Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com", "secretpassword")
    welcome_page.assert_popup_message("Account successfully register!")

    home_page = HomePage(driver)
    home_page.verify_user_info("Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com")


@pytest.mark.timeout(15)
def test_login_invalid_credentials(driver):
    driver.get("http://localhost:8080/")

    welcome_page = WelcomePage(driver)
    welcome_page.login("peter@parker.com", "secretpassword")
    welcome_page.assert_url_path("")
    welcome_page.assert_popup_message("Invalid username or password.")
