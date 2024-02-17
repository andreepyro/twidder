import time
from multiprocessing import Process

import pytest
from selenium import webdriver
from selenium.webdriver.support.ui import Select

from twidder.database_handler import initialize_database, clear_database
from twidder.server import app


@pytest.fixture(scope="module", autouse=True)
def run_server():
    server = Process(target=lambda: app.run(host="localhost", port=8080))
    server.start()
    time.sleep(1)  # wait for server to start
    yield
    server.terminate()
    server.join()


@pytest.fixture()
def driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5.0)
    _reset_database()
    yield driver
    driver.quit()


def test_sign_up(driver):
    # try to register user with empty first name
    driver.get("http://localhost:8080/")
    _register(driver, "", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com", "secretpassword", False)

    # try to register user with empty last name
    driver.get("http://localhost:8080/")
    _register(driver, "Peter", "", "Male", "Linkoping", "Sweden", "peter@parker.com", "secretpassword", False)

    # try to register user without selecting gender
    driver.get("http://localhost:8080/")
    _register(driver, "Peter", "Parker", "", "Linkoping", "Sweden", "peter@parker.com", "secretpassword", False)

    # try to register user with empty city
    driver.get("http://localhost:8080/")
    _register(driver, "Peter", "Parker", "Male", "", "Sweden", "peter@parker.com", "secretpassword", False)

    # try to register user with empty country
    driver.get("http://localhost:8080/")
    _register(driver, "Peter", "Parker", "Male", "Linkoping", "", "peter@parker.com", "secretpassword", False)

    # try to register user with invalid email
    driver.get("http://localhost:8080/")
    _register(driver, "Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker", "secretpassword", False)

    # try to register user with short password
    driver.get("http://localhost:8080/")
    _register(driver, "Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com", "short", False)

    # try to register user with empty password
    driver.get("http://localhost:8080/")
    _register(driver, "Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com", "", False)

    # try to register user with correct details
    driver.get("http://localhost:8080/")
    _register(driver, "Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com", "secretpassword", True)
    time.sleep(4.5)  # for pop-up message to disappear
    _logout(driver)

    # try to register a new user with already used email
    driver.get("http://localhost:8080/")
    _register(driver, "Lucy", "Boss", "Female", "Stockholm", "Sweden", "peter@parker.com", "totalysecretpaddowrd", False)


def test_sign_in(driver):
    # try to log in with invalid credentials
    driver.get("http://localhost:8080/")
    _login(driver, "random@email.com", "password", False)

    # create a new user
    driver.get("http://localhost:8080/")
    _register(driver, "Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com", "secretpassword", True)
    time.sleep(4.5)  # for pop-up message to disappear
    _logout(driver)

    # try to log in with invalid email
    driver.get("http://localhost:8080/")
    _login(driver, "random@email.com", "secretpassword", False)

    # try to log in with invalid password
    driver.get("http://localhost:8080/")
    _login(driver, "peter@parker.com", "password", False)

    # log in with valid credentials
    driver.get("http://localhost:8080/")


def test_browse_users(driver):
    # create first user and logout
    driver.get("http://localhost:8080/")
    _register(driver, "Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com", "secretpassword", True)
    time.sleep(4.5)  # for pop-up message to disappear
    _logout(driver)

    # create second user
    driver.get("http://localhost:8080/")
    _register(driver, "Adam", "Cool", "Other", "Copenhagen", "Denmark", "adam@cool.com", "longpassword", True)
    time.sleep(4.5)  # for pop-up message to disappear

    # switch to browse tab
    _switch_tab(driver, "browse")

    # browse user
    _browse_user(driver, "peter@parker.com", True)

    # check correct details
    _check_browse_tab_user_info(driver, "Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com")


def test_post_message(driver):
    # create a new user
    driver.get("http://localhost:8080/")
    _register(driver, "Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com", "secretpassword", True)
    time.sleep(4.5)  # for pop-up message to disappear

    # add several posts
    posts = ["hey!", "how are you?", "Hmmm, I like food"]
    for post in posts:
        _add_home_post(driver, "peter@parker.com", post)

    # reload page and check if posts still exist
    driver.get("http://localhost:8080/")
    time.sleep(1.0)  # wait until the app is loaded
    for post in posts:
        _check_post_exists(driver, "peter@parker.com", post)


def test_change_account_details(driver):
    # create a new user
    driver.get("http://localhost:8080/")
    _register(driver, "Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com", "secretpassword", True)
    time.sleep(4.5)  # for pop-up message to disappear

    # check current user details in home tab
    _check_home_tab_user_info(driver, "Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com")

    # switch to account tab
    _switch_tab(driver, "account")

    # change user details
    _update_user_details(driver, "Martin", "Boss", "Female", "Stockholm", "Sweden", True)
    time.sleep(4.5)  # for pop-up message to disappear

    # check new user details in home tab
    _switch_tab(driver, "home")
    _check_home_tab_user_info(driver, "Martin", "Boss", "Female", "Stockholm", "Sweden", "peter@parker.com")

    # reload and check user details again
    driver.get("http://localhost:8080/")
    time.sleep(1.0)  # wait until the app is loaded
    _check_home_tab_user_info(driver, "Martin", "Boss", "Female", "Stockholm", "Sweden", "peter@parker.com")


def _reset_database():
    with app.app_context():
        clear_database()
        initialize_database()


def _login(driver: webdriver.Chrome, email: str, password: str, expect_success: bool):
    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check user is not logged in
    assert driver.current_url == "http://localhost:8080/"

    # try log in with provided credentials
    input_email = driver.find_element("id", "input-login-email")
    input_email.clear()
    input_email.send_keys(email)

    input_password = driver.find_element("id", "input-login-password")
    input_password.clear()
    input_password.send_keys(password)

    submit_button = driver.find_element("id", "button-login")
    submit_button.click()

    # check operation result
    time.sleep(1)
    popup_message = driver.find_element("id", "pop-message")
    if expect_success:
        assert popup_message.value_of_css_property('visibility') == "hidden"
        assert popup_message.get_attribute('innerHTML') == ""
        assert driver.current_url == "http://localhost:8080/home"
    else:
        assert popup_message.value_of_css_property('visibility') == "visible"
        assert popup_message.get_attribute('innerHTML') == "Invalid username or password."
        assert driver.current_url == "http://localhost:8080/"


def _register(driver: webdriver.Chrome, firstname: str, lastname: str, gender: str, city: str, country: str, email: str, password: str, expect_success: bool):
    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check user is not logged in
    assert driver.current_url == "http://localhost:8080/"

    # check register window is closed
    assert driver.find_element("id", "register-container").value_of_css_property("display") == "none"

    # open register window
    driver.find_element("id", "button-register-window").click()

    # try to register new user
    input_firstname = driver.find_element("id", "input-sign-up-first-name")
    input_firstname.clear()
    input_firstname.send_keys(firstname)

    input_lastname = driver.find_element("id", "input-sign-up-last-name")
    input_lastname.clear()
    input_lastname.send_keys(lastname)

    select_gender = Select(driver.find_element("id", "input-sign-up-gender"))
    if gender:
        select_gender.select_by_visible_text(gender)

    input_city = driver.find_element("id", "input-sign-up-city")
    input_city.clear()
    input_city.send_keys(city)

    input_country = driver.find_element("id", "input-sign-up-country")
    input_country.clear()
    input_country.send_keys(country)

    input_email = driver.find_element("id", "input-sign-up-email")
    input_email.clear()
    input_email.send_keys(email)

    input_password = driver.find_element("id", "input-sign-up-password")
    input_password.clear()
    input_password.send_keys(password)

    input_password_repeat = driver.find_element("id", "input-sign-up-password-repeat")
    input_password_repeat.clear()
    input_password_repeat.send_keys(password)

    submit_button = driver.find_element("id", "button-register")
    submit_button.click()

    # check operation result
    time.sleep(1)
    popup_message = driver.find_element("id", "pop-message")
    if expect_success:
        assert driver.current_url == "http://localhost:8080/home"
        assert popup_message.value_of_css_property('visibility') == "visible"
        assert popup_message.get_attribute('innerHTML') == "Account successfully register!"
    else:
        assert driver.current_url == "http://localhost:8080/"


def _logout(driver: webdriver.Chrome):
    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check we are logged in
    assert driver.current_url != "http://localhost:8080/"

    # log out
    submit_button = driver.find_element("id", "button-logout")
    submit_button.click()

    # check success
    time.sleep(1)
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "visible"
    assert popup_message.get_attribute('innerHTML') == "You have successfully logged out."
    assert driver.current_url == "http://localhost:8080/"


def _check_home_tab_user_info(driver: webdriver.Chrome, firstname: str, lastname: str, gender: str, city: str, country: str, email: str):
    # check home tab is loaded
    assert driver.current_url == "http://localhost:8080/home"

    # check user information
    assert driver.find_element("id", "home-user-name").get_attribute('innerHTML') == f"{firstname} {lastname}"
    assert driver.find_element("id", "home-user-gender").get_attribute('innerHTML') == gender
    assert driver.find_element("id", "home-user-email").get_attribute('innerHTML') == email
    assert driver.find_element("id", "home-user-location").get_attribute('innerHTML') == f"{city}, {country}"


def _check_browse_tab_user_info(driver: webdriver.Chrome, firstname: str, lastname: str, gender: str, city: str, country: str, email: str):
    # check home tab is loaded
    assert driver.current_url == f"http://localhost:8080/browse?email={email}"

    # check user information
    assert driver.find_element("id", "browse-user-name").get_attribute('innerHTML') == f"{firstname} {lastname}"
    assert driver.find_element("id", "browse-user-gender").get_attribute('innerHTML') == gender
    assert driver.find_element("id", "browse-user-email").get_attribute('innerHTML') == email
    assert driver.find_element("id", "browse-user-location").get_attribute('innerHTML') == f"{city}, {country}"


def _switch_tab(driver: webdriver.Chrome, tab_name: str):
    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check we are logged in
    assert driver.current_url != "http://localhost:8080/"

    # switch tab
    driver.find_element("id", f"sidebar-tab-{tab_name}").click()

    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check success
    assert driver.current_url == f"http://localhost:8080/{tab_name}"


def _browse_user(driver: webdriver.Chrome, email: str, expect_success: bool):
    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check user is in the correct tab
    assert driver.current_url == "http://localhost:8080/browse"

    # try log in with provided credentials
    input_email = driver.find_element("id", "input-user-email")
    input_email.clear()
    input_email.send_keys(email)

    search_button = driver.find_element("id", "browse-search-button")
    search_button.click()

    # check operation result
    time.sleep(1)
    assert driver.current_url == f"http://localhost:8080/browse?email={email}"
    popup_message = driver.find_element("id", "pop-message")
    if expect_success:
        assert popup_message.value_of_css_property('visibility') == "hidden"
        assert popup_message.get_attribute('innerHTML') == ""
    else:
        assert popup_message.value_of_css_property('visibility') == "visible"
        assert popup_message.get_attribute('innerHTML') == "User not found."


def _add_home_post(driver: webdriver.Chrome, email: str, content: str):
    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check we are on home page
    assert driver.current_url == "http://localhost:8080/home"

    # add post
    input_post = driver.find_element("id", "input-home-new-post")
    input_post.clear()
    input_post.send_keys(content)

    submit_button = driver.find_element("id", "button-home-new-post")
    submit_button.click()

    # wait for the request
    time.sleep(1)

    # check post exists and they're correct
    _check_post_exists(driver, email, content)


def _check_post_exists(driver: webdriver.Chrome, email: str, content: str):
    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check we are on home page
    assert driver.current_url == "http://localhost:8080/home"

    # check post exists
    posts = driver.find_elements("xpath", "//div[@class='user-post']")
    for post in posts:
        if post.find_element("class name", "author").get_attribute('innerHTML') == email and post.find_element("class name", "content").get_attribute(
                'innerHTML') == content.replace("\n", "<br>") + "<br>":
            break
    else:
        assert False  # post not found!


def _update_user_details(driver: webdriver.Chrome, firstname: str, lastname: str, gender: str, city: str, country: str, expect_success: bool):
    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check account tab is loaded
    assert driver.current_url == "http://localhost:8080/account"

    # fill new account details
    input_firstname = driver.find_element("id", "input-account-first-name")
    input_firstname.clear()
    input_firstname.send_keys(firstname)

    input_lastname = driver.find_element("id", "input-account-last-name")
    input_lastname.clear()
    input_lastname.send_keys(lastname)

    select_gender = Select(driver.find_element("id", "input-account-gender"))
    if gender:
        select_gender.select_by_visible_text(gender)

    input_city = driver.find_element("id", "input-account-city")
    input_city.clear()
    input_city.send_keys(city)

    input_country = driver.find_element("id", "input-account-country")
    input_country.clear()
    input_country.send_keys(country)

    submit_button = driver.find_element("id", "button-update-account-details")
    submit_button.click()

    # check operation result
    time.sleep(1)
    popup_message = driver.find_element("id", "pop-message")
    if expect_success:
        assert driver.current_url == "http://localhost:8080/account"
        assert popup_message.value_of_css_property('visibility') == "visible"
        assert popup_message.get_attribute('innerHTML') == "Account details successfully changed!"
    else:
        assert driver.current_url == "http://localhost:8080/account"
        assert popup_message.value_of_css_property('visibility') == "visible"
        assert popup_message.get_attribute('innerHTML') == "error"
