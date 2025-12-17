"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Test the /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that getting activities returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that activities endpoint returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_activities_contain_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        assert len(activities) > 0, "Should have at least one activity"
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_have_known_activities(self):
        """Test that expected activities are present"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in activities


class TestSignupEndpoint:
    """Test the /activities/{activity_name}/signup endpoint"""

    def test_signup_with_valid_data(self):
        """Test signing up with valid email and activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]

    def test_signup_duplicate_email_returns_400(self):
        """Test that signing up twice with same email returns 400"""
        email = "duplicate@mergington.edu"
        activity = "Chess%20Club"
        
        # First signup should succeed
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_invalid_activity_returns_404(self):
        """Test that signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_signup_adds_participant_to_list(self):
        """Test that signup adds the participant to the activity's participant list"""
        email = "newparticipant@mergington.edu"
        activity = "Programming%20Class"
        
        # Get initial participant count
        response1 = client.get("/activities")
        initial_participants = response1.json()["Programming Class"]["participants"].copy()
        
        # Sign up
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 200
        
        # Check participant list was updated
        response3 = client.get("/activities")
        updated_participants = response3.json()["Programming Class"]["participants"]
        assert email in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1


class TestUnregisterEndpoint:
    """Test the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_with_valid_data(self):
        """Test unregistering with valid email and activity"""
        # First sign up a participant
        email = "unregister@mergington.edu"
        activity = "Chess%20Club"
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Now unregister
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister removes the participant from the list"""
        email = "removetest@mergington.edu"
        activity = "Programming%20Class"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify participant is in the list
        response1 = client.get("/activities")
        assert email in response1.json()["Programming Class"]["participants"]
        
        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Verify participant is removed
        response2 = client.get("/activities")
        assert email not in response2.json()["Programming Class"]["participants"]

    def test_unregister_non_participant_returns_400(self):
        """Test that unregistering a non-participant returns 400"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=notasignup@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_invalid_activity_returns_404(self):
        """Test that unregistering from non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirects(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]
