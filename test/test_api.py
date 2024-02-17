import http
from multiprocessing import Process

import pytest
import time
import requests

from twidder.database_handler import initialize_database, clear_database
from twidder.server import app


@pytest.fixture(scope="module", autouse=True)
def run_server():
    with app.app_context():
        clear_database()
        initialize_database()

    server = Process(target=lambda: app.run(host="localhost", port=8080))
    server.start()
    time.sleep(1)  # wait for server to start
    yield
    server.terminate()
    server.join()


@pytest.mark.skip("Not implemented yet")
def test_invalid_api_route():
    response = requests.get("http://localhost:8080/api/v1/nonexisting/route")
    assert response.status_code == http.HTTPStatus.NOT_FOUND
    # make sure generic NOT FOUND page is shown (not the custom page for frontend)
    assert response.text == "<!doctype html>\n<html lang=en>\n<title>404 Not Found</title>\n<h1>Not Found</h1>\n<p>The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.</p>\n"


def test_invalid_general_route():
    response = requests.get("http://localhost:8080/nonexisting/route")
    assert response.status_code == http.HTTPStatus.OK
    # make sure custom NOT FOUND page is shown
    assert response.text != "<!doctype html>\n<html lang=en>\n<title>404 Not Found</title>\n<h1>Not Found</h1>\n<p>The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.</p>\n"
