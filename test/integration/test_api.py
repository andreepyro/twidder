import http
import json
import time
import hmac
import uuid
import base64
import hashlib
from multiprocessing import Process

import pytest
import requests

from twidder.database_handler import initialize_database, clear_database
from twidder.server import app


BASE_URL = "http://localhost:8080/api/v1"

def get_authorization_header(user_email, session_id, payload=None):
    message = json.dumps(payload) if payload is not None else ""
    hmac_obj = hmac.new(
        session_id.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    hash_hex = hmac_obj.hexdigest()
    auth_obj = {
        "email": user_email,
        "hash": hash_hex
    }
    return base64.b64encode(json.dumps(auth_obj).encode('utf-8')).decode('utf-8')

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

@pytest.fixture
def test_user():
    return {
        "firstname": "Test",
        "lastname": "User",
        "gender": "Other",
        "city": "Test City",
        "country": "Test Country",
        "email": f"{uuid.uuid4()}@example.com",
        "password": "testpassword123",
        "image": "base64encodedimage"
    }

@pytest.fixture
def session_data(test_user):
    # create user
    response = requests.post(f"{BASE_URL}/users", json=test_user)
    assert response.status_code == http.HTTPStatus.CREATED, print(response.content)
    
    # create user sessions
    response = requests.post(f"{BASE_URL}/session", json={
        "email": test_user["email"],
        "password": test_user["password"]
    })
    assert response.status_code == http.HTTPStatus.CREATED, print(response.content)

    # yield the session
    session_id = response.headers["Authorization"]
    data = {
        "email": test_user["email"],
        "session_id": session_id
    }
    yield data

    # delete user
    auth_header = get_authorization_header(
        data["email"],
        data["session_id"]
    )
    headers = {"Authorization": f"{auth_header}"}
    response = requests.delete(f"{BASE_URL}/users/{data['email']}", headers=headers)
    assert response.status_code == http.HTTPStatus.OK, print(response.content)

# Session Tests
def test_create_session_success(test_user):
    # Create user first
    requests.post(f"{BASE_URL}/users", json=test_user)
    
    response = requests.post(f"{BASE_URL}/session", json={
        "email": test_user["email"],
        "password": test_user["password"]
    })
    assert response.status_code == http.HTTPStatus.CREATED, print(response.content)
    assert "Authorization" in response.headers, print(response.content)

def test_create_session_invalid_credentials():
    response = requests.post(f"{BASE_URL}/session", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == http.HTTPStatus.UNAUTHORIZED, print(response.content)

def test_delete_session_success(test_user):
    response = requests.post(f"{BASE_URL}/users", json=test_user)
    assert response.status_code == http.HTTPStatus.CREATED, print(response.content)

    response = requests.post(f"{BASE_URL}/session", json={
        "email": test_user["email"],
        "password": test_user["password"]
    })
    assert response.status_code == http.HTTPStatus.CREATED, print(response.content)

    session_id = response.headers["Authorization"]
    auth_header = get_authorization_header(
        test_user["email"],
        session_id
    )
    headers = {"Authorization": f"{auth_header}"}
    response = requests.delete(f"{BASE_URL}/session", headers=headers)
    assert response.status_code == http.HTTPStatus.OK, print(response.content)

def test_delete_session_unauthorized():
    response = requests.delete(f"{BASE_URL}/session")
    assert response.status_code == http.HTTPStatus.UNAUTHORIZED, print(response.content)

# User Tests
def test_create_user_success(test_user):
    response = requests.post(f"{BASE_URL}/users", json=test_user)
    assert response.status_code == http.HTTPStatus.CREATED, print(response.content)

def test_create_user_duplicate_email(test_user):
    response = requests.post(f"{BASE_URL}/users", json=test_user)
    assert response.status_code == http.HTTPStatus.CREATED, print(response.content)
    
    response = requests.post(f"{BASE_URL}/users", json=test_user)
    assert response.status_code == http.HTTPStatus.CONFLICT, print(response.content)

def test_get_user_success(test_user, session_data):
    auth_header = get_authorization_header(
        session_data["email"],
        session_data["session_id"]
    )
    headers = {"Authorization": f"{auth_header}"}
    response = requests.get(f"{BASE_URL}/users/{test_user['email']}", headers=headers)
    assert response.status_code == http.HTTPStatus.OK, print(response.content)
    user_data = response.json()
    assert user_data["email"] == test_user["email"], print(response.content)
    assert user_data["firstname"] == test_user["firstname"], print(response.content)

def test_get_user_unauthorized(test_user):
    response = requests.get(f"{BASE_URL}/users/{test_user['email']}")
    assert response.status_code == http.HTTPStatus.UNAUTHORIZED, print(response.content)

def test_update_user_success(test_user, session_data):
    updated_data = test_user.copy()
    updated_data["city"] = "Updated City"
    updated_data.pop("email")
    
    auth_header = get_authorization_header(
        session_data["email"],
        session_data["session_id"],
        updated_data
    )
    headers = {"Authorization": f"{auth_header}"}
    
    response = requests.patch(
        f"{BASE_URL}/users/{test_user['email']}", 
        headers=headers,
        json=updated_data
    )
    assert response.status_code == http.HTTPStatus.OK, print(response.content)

def test_update_user_unauthorized(test_user):
    response = requests.patch(f"{BASE_URL}/users/{test_user['email']}", json=test_user)
    assert response.status_code == http.HTTPStatus.UNAUTHORIZED, print(response.content)

def test_delete_user_success(test_user):
    response = requests.post(f"{BASE_URL}/users", json=test_user)
    assert response.status_code == http.HTTPStatus.CREATED, print(response.content)

    response = requests.post(f"{BASE_URL}/session", json={
        "email": test_user["email"],
        "password": test_user["password"]
    })
    assert response.status_code == http.HTTPStatus.CREATED, print(response.content)

    session_id = response.headers["Authorization"]
    auth_header = get_authorization_header(
        test_user["email"],
        session_id
    )
    headers = {"Authorization": f"{auth_header}"}
    response = requests.delete(f"{BASE_URL}/users/{test_user['email']}", headers=headers)
    assert response.status_code == http.HTTPStatus.OK, print(response.content)

def test_delete_user_unauthorized(test_user):
    response = requests.delete(f"{BASE_URL}/users/{test_user['email']}")
    assert response.status_code == http.HTTPStatus.UNAUTHORIZED, print(response.content)

# Posts Tests
def test_create_post_success(test_user, session_data):
    post_data = {
        "email": test_user["email"],
        "message": "Test post message",
        "media": "base64encodedmedia"
    }
    
    auth_header = get_authorization_header(
        session_data["email"],
        session_data["session_id"],
        post_data
    )
    headers = {"Authorization": f"{auth_header}"}
    
    response = requests.post(f"{BASE_URL}/posts", headers=headers, json=post_data)
    assert response.status_code == http.HTTPStatus.CREATED, print(response.content)
    assert "id" in response.json(), print(response.content)
    assert response.json()["id"]

def test_create_post_unauthorized():
    post_data = {
        "email": "test@example.com",
        "message": "Test post message",
        "media": "base64encodedmedia"
    }
    response = requests.post(f"{BASE_URL}/posts", json=post_data)
    assert response.status_code == http.HTTPStatus.UNAUTHORIZED, print(response.content)

def test_get_posts_success(test_user, session_data):
    auth_header = get_authorization_header(
        session_data["email"],
        session_data["session_id"]
    )
    headers = {"Authorization": f"{auth_header}"}
    response = requests.get(
        f"{BASE_URL}/posts",
        params={"user_email": test_user["email"]},
        headers=headers
    )
    assert response.status_code == http.HTTPStatus.OK, print(response.content)
    assert "posts" in response.json(), print(response.content)

def test_get_posts_unauthorized():
    response = requests.get(f"{BASE_URL}/posts")
    assert response.status_code == http.HTTPStatus.UNAUTHORIZED, print(response.content)

def test_update_post_success(test_user, session_data):
    # Create a post first
    post_data = {
        "email": test_user["email"],
        "message": "Original content",
        "media": "base64encodedmedia"
    }
    
    create_auth_header = get_authorization_header(
        session_data["email"],
        session_data["session_id"],
        post_data
    )
    headers = {"Authorization": f"{create_auth_header}"}
    create_response = requests.post(f"{BASE_URL}/posts", headers=headers, json=post_data)
    post_id = create_response.json()["id"]
    
    # Update the post
    update_data = {
        "message": "Updated content",
        "media": "newbase64encodedmedia"
    }
    
    update_auth_header = get_authorization_header(
        session_data["email"],
        session_data["session_id"],
        update_data
    )
    headers = {"Authorization": f"{update_auth_header}"}
    
    response = requests.patch(
        f"{BASE_URL}/posts/{post_id}",
        headers=headers,
        json=update_data
    )
    assert response.status_code == http.HTTPStatus.OK, print(response.content)

def test_update_post_unauthorized():
    post_id = "some-post-id"
    update_data = {
        "message": "Updated content",
        "media": "newbase64encodedmedia"
    }
    response = requests.patch(f"{BASE_URL}/posts/{post_id}", json=update_data)
    assert response.status_code == http.HTTPStatus.UNAUTHORIZED, print(response.content)

def test_delete_post_success(test_user, session_data):
    # Create a post first
    post_data = {
        "email": test_user["email"],
        "message": "To be deleted",
        "media": "base64encodedmedia"
    }
    
    create_auth_header = get_authorization_header(
        session_data["email"],
        session_data["session_id"],
        post_data
    )
    headers = {"Authorization": f"{create_auth_header}"}
    create_response = requests.post(f"{BASE_URL}/posts", headers=headers, json=post_data)
    post_id = create_response.json()["id"]
    
    # Delete the post
    delete_auth_header = get_authorization_header(
        session_data["email"],
        session_data["session_id"]
    )
    headers = {"Authorization": f"{delete_auth_header}"}
    response = requests.delete(f"{BASE_URL}/posts/{post_id}", headers=headers)
    assert response.status_code == http.HTTPStatus.OK, print(response.content)

def test_delete_post_unauthorized():
    post_id = "some-post-id"
    response = requests.delete(f"{BASE_URL}/posts/{post_id}")
    assert response.status_code == http.HTTPStatus.UNAUTHORIZED, print(response.content)

def test_invalid_api_route():
    response = requests.get(f"{BASE_URL}/nonexisting/route")
    assert response.status_code == http.HTTPStatus.BAD_REQUEST, print(response.content)
    assert response.json() == {"message": "bad request"}, print(response.content)

def test_invalid_general_route():
    response = requests.get("http://localhost:8080/nonexisting/route")
    assert response.status_code == http.HTTPStatus.OK, print(response.content)
