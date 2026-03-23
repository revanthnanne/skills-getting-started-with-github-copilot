"""
Test suite for Mergington High School Activities API

Tests follow the AAA (Arrange-Act-Assert) pattern for clarity and maintainability.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Re-import to get fresh state
    import importlib
    import app as app_module
    importlib.reload(app_module)
    yield


class TestGetActivities:
    """Test suite for the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """
        ARRANGE: Create a test client
        ACT: Make GET request to /activities
        ASSERT: Verify response contains all activities
        """
        # Arrange - already done by fixture
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert len(data) >= 9  # At least 9 activities

    def test_get_activities_contains_required_fields(self, client):
        """
        ARRANGE: Create a test client
        ACT: Make GET request to /activities
        ASSERT: Verify each activity has required fields
        """
        # Arrange
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignupEndpoint:
    """Test suite for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student_succeeds(self, client):
        """
        ARRANGE: Prepare test data with new student
        ACT: Sign up the student for an activity
        ASSERT: Verify signup is successful
        """
        # Arrange
        activity_name = "Basketball Team"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert email in data["message"]

    def test_signup_duplicate_student_fails(self, client):
        """
        ARRANGE: Sign up a student once
        ACT: Try to sign up the same student again
        ASSERT: Verify duplicate signup is rejected
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_invalid_activity_fails(self, client):
        """
        ARRANGE: Prepare test data with non-existent activity
        ACT: Try to sign up for invalid activity
        ASSERT: Verify 404 error is returned
        """
        # Arrange
        activity_name = "Non-Existent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_signup_adds_participant_to_list(self, client):
        """
        ARRANGE: Prepare to sign up a new student
        ACT: Sign up student and verify in activities list
        ASSERT: Verify participant appears in activity
        """
        # Arrange
        activity_name = "Swimming Club"
        email = "swimmer@mergington.edu"
        
        # Act - Get initial state
        initial = client.get("/activities").json()
        initial_count = len(initial[activity_name]["participants"])
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert signup_response.status_code == 200
        
        # Verify participant was added
        updated = client.get("/activities").json()
        assert email in updated[activity_name]["participants"]
        assert len(updated[activity_name]["participants"]) == initial_count + 1


class TestUnregisterEndpoint:
    """Test suite for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_succeeds(self, client):
        """
        ARRANGE: Prepare with an existing participant
        ACT: Unregister the participant
        ASSERT: Verify unregister is successful
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_nonexistent_participant_fails(self, client):
        """
        ARRANGE: Prepare to unregister a participant who isn't signed up
        ACT: Try to unregister non-existent participant
        ASSERT: Verify 400 error is returned
        """
        # Arrange
        activity_name = "Art Studio"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_invalid_activity_fails(self, client):
        """
        ARRANGE: Prepare to unregister from non-existent activity
        ACT: Try to unregister from invalid activity
        ASSERT: Verify 404 error is returned
        """
        # Arrange
        activity_name = "Non-Existent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_unregister_removes_participant_from_list(self, client):
        """
        ARRANGE: Prepare with a signed-up participant
        ACT: Sign up, then unregister participant
        ASSERT: Verify participant no longer in list
        """
        # Arrange
        activity_name = "Drama Club"
        email = "actor@mergington.edu"
        
        # Act - Sign up first
        client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Verify they were added
        after_signup = client.get("/activities").json()
        assert email in after_signup[activity_name]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert unregister_response.status_code == 200
        
        # Verify participant was removed
        after_unregister = client.get("/activities").json()
        assert email not in after_unregister[activity_name]["participants"]


class TestParticipantCapacity:
    """Test suite for participant capacity constraints"""

    def test_activity_respects_max_participants(self, client):
        """
        ARRANGE: Check activity capacity
        ACT: Try to sign up multiple students
        ASSERT: Verify max_participants field is respected
        """
        # Arrange
        response = client.get("/activities")
        data = response.json()
        
        # Assert - Every activity should have max_participants
        for activity_name, activity_details in data.items():
            assert activity_details["max_participants"] > 0
            current_count = len(activity_details["participants"])
            assert current_count <= activity_details["max_participants"]


class TestRootEndpoint:
    """Test suite for the root endpoint"""

    def test_root_redirects_to_index(self, client):
        """
        ARRANGE: Create a test client
        ACT: Make GET request to /
        ASSERT: Verify redirect to /static/index.html
        """
        # Arrange
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]
