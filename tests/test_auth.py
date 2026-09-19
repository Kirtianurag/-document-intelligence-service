def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@pragatibharati.edu", "password": "Password123!"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@pragatibharati.edu"
    assert "id" in data


def test_register_duplicate_email(client, test_user):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": test_user.email, "password": "Password123!"}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(client, test_user):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": "SecretPassword123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client, test_user):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": "WrongPassword!"}
    )
    assert response.status_code == 401
