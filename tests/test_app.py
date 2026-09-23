import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = copy.deepcopy(activities)

    yield

    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index():
    # Arrange
    client = TestClient(app, follow_redirects=False)

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert "Chess Club" in response.json()
    chess_club = response.json()["Chess Club"]
    assert chess_club["description"] == "Learn strategies and compete in chess tournaments"
    assert chess_club["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert chess_club["max_participants"] == 12
    assert chess_club["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_student_to_activity():
    # Arrange
    client = TestClient(app)
    email = "student@mergington.edu"

    # Act
    response = client.post("/activities/Soccer Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Signed up student@mergington.edu for Soccer Club"}
    assert email in activities["Soccer Club"]["participants"]


def test_signup_rejects_unknown_activity():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_student():
    # Arrange
    client = TestClient(app)
    email = "michael@mergington.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert activities["Chess Club"]["participants"].count(email) == 1


def test_signup_requires_email():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.post("/activities/Soccer Club/signup")

    # Assert
    assert response.status_code == 422


def test_unregister_removes_student_from_activity():
    # Arrange
    client = TestClient(app)
    email = "michael@mergington.edu"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered michael@mergington.edu from Chess Club"
    }
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_rejects_unknown_activity():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_student_not_signed_up():
    # Arrange
    client = TestClient(app)
    email = "student@mergington.edu"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_requires_email():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.delete("/activities/Chess Club/signup")

    # Assert
    assert response.status_code == 422