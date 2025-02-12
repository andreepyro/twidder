import time
import socket
import pytest

from multiprocessing import Process
from selenium import webdriver

from twidder.database_handler import initialize_database, clear_database
from twidder.server import app


def _is_server_running(host, port):
    """Check if the server is running by attempting to connect to the host and port."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except (ConnectionRefusedError, socket.timeout):
        return False


def _reset_database():
    with app.app_context():
        clear_database()
        initialize_database()


@pytest.fixture(scope="module", autouse=True)
def run_server():
    server = Process(target=lambda: app.run(host="localhost", port=8080))
    server.start()

    for _ in range(10):  # wait 10 seconds for the server to start up (usually should take only aroun 1s)
        if _is_server_running("localhost", 8080):
            break
        time.sleep(1)
    else:
        raise RuntimeError("Server did not start within the expected time.")

    yield
    server.terminate()
    server.join()


@pytest.fixture()
def driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")  # https://stackoverflow.com/a/50725918/1689770
    chrome_options.add_argument("--disable-browser-side-navigation")  # https://stackoverflow.com/a/49123152/1689770
    chrome_options.add_argument("--disable-gpu")  # https://stackoverflow.com/questions/51959986/
    chrome_options.add_argument("start-maximized")  # https://stackoverflow.com/a/26283818/1689770
    chrome_options.add_argument("enable-automation")  # https://stackoverflow.com/a/43840128/1689770
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5.0)
    _reset_database()
    yield driver
    driver.quit()
