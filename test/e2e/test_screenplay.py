import pytest

from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By

from test.e2e.utils import run_server, driver


# Actor
class Actor:
    def __init__(self, name, browser):
        self.name = name
        self.browser = browser

    def can(self, ability):
        setattr(self, ability.__class__.__name__.lower(), ability)

    def attempts_to(self, task):
        task.perform_as(self)


# Abilities
class BrowseTheWeb:
    def __init__(self, browser):
        self.browser = browser


# Tasks
class NavigateTo:
    def __init__(self, url):
        self.url = url

    def perform_as(self, actor):
        actor.browsetheweb.browser.get(self.url)


class RegisterUser:
    def __init__(self, firstname, lastname, gender, city, country, email, password, expect_success):
        self.firstname = firstname
        self.lastname = lastname
        self.gender = gender
        self.city = city
        self.country = country
        self.email = email
        self.password = password
        self.expect_success = expect_success

    def perform_as(self, actor):
        browser = actor.browsetheweb.browser

        # open registration form
        browser.find_element(By.ID, "button-register-window").click()

        # fill out form fields
        browser.find_element(By.ID, "input-sign-up-first-name").send_keys(self.firstname)
        browser.find_element(By.ID, "input-sign-up-last-name").send_keys(self.lastname)
        if self.gender:
            Select(browser.find_element(By.ID, "input-sign-up-gender")).select_by_visible_text(self.gender)
        browser.find_element(By.ID, "input-sign-up-city").send_keys(self.city)
        browser.find_element(By.ID, "input-sign-up-country").send_keys(self.country)
        browser.find_element(By.ID, "input-sign-up-email").send_keys(self.email)
        browser.find_element(By.ID, "input-sign-up-password").send_keys(self.password)
        browser.find_element(By.ID, "input-sign-up-password-repeat").send_keys(self.password)

        # submit form
        browser.find_element(By.ID, "button-register").click()

        # validate outcome
        popup_message = browser.find_element(By.ID, "pop-message")
        WebDriverWait(driver, timeout=2).until(lambda _: popup_message.value_of_css_property('visibility') == "visible")
        if self.expect_success:
            assert popup_message.get_attribute('innerHTML') == "Account successfully register!"
        else:
            assert "error" in popup_message.get_attribute('innerHTML').lower()
        WebDriverWait(driver, timeout=5).until(lambda _: popup_message.value_of_css_property('visibility') == "hidden")


@pytest.mark.timeout(15)
def test_register_user(driver):
    actor = Actor("Test User", driver)
    actor.can(BrowseTheWeb(driver))

    actor.attempts_to(NavigateTo("http://localhost:8080/"))
    actor.attempts_to(RegisterUser(
        firstname="Peter",
        lastname="Parker",
        gender="Male",
        city="Linkoping",
        country="Sweden",
        email="peter@parker.com",
        password="secretpassword",
        expect_success=True
    ))
