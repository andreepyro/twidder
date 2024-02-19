import http
import time
from multiprocessing import Process

import pytest
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


def test_invalid_api_route():
    # make sure that non-existent /api requests fail with BAD_REQUEST response
    response = requests.get("http://localhost:8080/api/v1/nonexisting/route")
    assert response.status_code == http.HTTPStatus.BAD_REQUEST
    assert response.json() == {"message": "bad request"}


def test_invalid_general_route():
    # make sure that non-existent page succeeds with OK response
    response = requests.get("http://localhost:8080/nonexisting/route")
    assert response.status_code == http.HTTPStatus.OK
