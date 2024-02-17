import time
from multiprocessing import Process

import pytest
from selenium import webdriver

from twidder.server import app


@pytest.fixture(scope="session", autouse=True)
def run_server():
    server = Process(target=lambda: app.run(host="localhost", port=8080))
    server.start()
    yield
    server.terminate()
    server.join()


def test_e2e_workflow():
    # create drive
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("http://127.0.0.1:8080/")

    driver.implicitly_wait(5.0)

    # try to log in with invalid credentials
    _login(driver, "random@email.com", "password", False)

    # register new user
    _register(driver, "Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com", "secretpassword", True)

    # check user information in home tab
    _check_home_tab_user_info(driver, "Peter", "Parker", "Male", "Linkoping", "Sweden", "peter@parker.com")

    # check url is the same after page refresh
    old_url = driver.current_url
    driver.get("http://127.0.0.1:8080/")
    assert driver.current_url == old_url

    # log out
    _logout(driver)

    # try to register a new user with the same email
    _register(driver, "Anna", "Great", "Female", "Stockholm", "Sweden", "peter@parker.com", "anotherpassword", False)

    # try to register a new user with a new email
    _register(driver, "Anna", "Great", "Female", "Stockholm", "Sweden", "anna@great.com", "anotherpassword", True)

    # check user information in home tab
    _check_home_tab_user_info(driver, "Anna", "Great", "Female", "Stockholm", "Sweden", "anna@great.com")

    # add several posts
    anna_posts = ["hey!", "how are you?", "hmmm, I like food"]
    for post in anna_posts:
        _add_home_post(driver, "anna@great.com", post)

    # TODO add post on Peter's wall

    # log out
    _logout(driver)

    # try to log in with invalid credentials
    _login(driver, "peter@parker.com", "anotherpassword", False)

    # try to log in with invalid credentials
    _login(driver, "anna@great.com", "secretpassword", False)

    # try to log in with valid credentials
    _login(driver, "peter@parker.com", "secretpassword", True)

    # switch tabs several times
    _switch_tab(driver, "home")
    _switch_tab(driver, "browse")
    _switch_tab(driver, "account")
    _switch_tab(driver, "account")
    _switch_tab(driver, "home")
    _switch_tab(driver, "account")
    _switch_tab(driver, "home")

    # add several posts
    peter_posts = ["hello", "this is my second post!"]
    for post in peter_posts:
        _add_home_post(driver, "peter@parker.com", post)

    # browse for another user
    _switch_tab(driver, "browse")
    # TODO browse for Anna

    # TODO check Anna's posts

    # TODO add post on Anna's wall

    # TODO add new posts to Anna's wall

    driver.quit()


def _login(driver: webdriver.Chrome, email: str, password: str, expect_success: bool):
    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check user is not logged in
    assert driver.current_url == "http://127.0.0.1:8080/"

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
    popup_message = driver.find_element("id", "pop-message")
    if expect_success:
        assert popup_message.value_of_css_property('visibility') == "hidden"
        assert popup_message.get_attribute('innerHTML') == ""
        assert driver.current_url == "http://127.0.0.1:8080/home"
    else:
        assert popup_message.value_of_css_property('visibility') == "visible"
        assert popup_message.get_attribute('innerHTML') == "Wrong username or password."
        assert driver.current_url == "http://127.0.0.1:8080/"
        time.sleep(5.0)  # wait for popup message to disappear


def _register(driver: webdriver.Chrome, firstname: str, lastname: str, gender: str, city: str, country: str, email: str, password: str, expect_success: bool):
    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check user is not logged in
    assert driver.current_url == "http://127.0.0.1:8080/"

    # try to register new user
    input_firstname = driver.find_element("id", "input-sign-up-first-name")
    input_firstname.clear()
    input_firstname.send_keys(firstname)

    input_lastname = driver.find_element("id", "input-sign-up-last-name")
    input_lastname.clear()
    input_lastname.send_keys(lastname)

    input_gender = driver.find_element("id", "input-sign-up-gender")
    input_gender.send_keys(gender)

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
    popup_message = driver.find_element("id", "pop-message")
    if expect_success:
        assert popup_message.value_of_css_property('visibility') == "hidden"
        assert popup_message.get_attribute('innerHTML') == ""
        assert driver.current_url == "http://127.0.0.1:8080/home"
    else:
        assert popup_message.value_of_css_property('visibility') == "visible"
        assert popup_message.get_attribute('innerHTML') == "User already exists."
        assert driver.current_url == "http://127.0.0.1:8080/"
        time.sleep(5.0)  # wait for popup message to disappear


def _logout(driver: webdriver.Chrome):
    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check we are logged in
    assert driver.current_url != "http://127.0.0.1:8080/"

    # log out
    submit_button = driver.find_element("id", "button-logout")
    submit_button.click()

    # check success
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"
    driver.get("http://127.0.0.1:8080/")  # reload, TODO REMOVE THIS !!!
    assert driver.current_url == "http://127.0.0.1:8080/"


def _check_home_tab_user_info(driver: webdriver.Chrome, firstname: str, lastname: str, gender: str, city: str, country: str, email: str):
    # check home tab is loaded
    assert driver.current_url == "http://127.0.0.1:8080/home"

    # check user information
    assert driver.find_element("id", "home-user-name").get_attribute('innerHTML') == f"{firstname} {lastname}"
    assert driver.find_element("id", "home-user-gender").get_attribute('innerHTML') == gender
    assert driver.find_element("id", "home-user-email").get_attribute('innerHTML') == email
    assert driver.find_element("id", "home-user-location").get_attribute('innerHTML') == f"{city}, {country}"


def _switch_tab(driver: webdriver.Chrome, tabname: str):
    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check we are logged in
    assert driver.current_url != "http://127.0.0.1:8080/"

    # switch tab
    driver.find_element("id", f"sidebar-tab-{tabname}").click()

    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check success
    assert driver.current_url == f"http://127.0.0.1:8080/{tabname}"


def _add_home_post(driver: webdriver.Chrome, email: str, content: str):
    # check popup message is not visible
    popup_message = driver.find_element("id", "pop-message")
    assert popup_message.value_of_css_property('visibility') == "hidden"

    # check we are on home page
    assert driver.current_url == "http://127.0.0.1:8080/home"

    # add post
    input_post = driver.find_element("id", "input-home-new-post")
    input_post.clear()
    input_post.send_keys(content)

    submit_button = driver.find_element("id", "button-home-new-post")
    submit_button.click()

    # check post exists
    posts = driver.find_elements("xpath", "//div[@class='home-post']")
    for post in posts:
        if post.find_element("class name", "author").get_attribute('innerHTML') == email and post.find_element("class name", "content").get_attribute(
                'innerHTML') == content:
            break
    else:
        assert False  # post not found!
