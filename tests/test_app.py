"""
Tests for the Mergington High School Activities API
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Test the /activities endpoint"""

    def test_get_activities(self):
        """Test that we can retrieve all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        
        # Verify activity structure
        for activity_name, activity_details in activities.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_activities_contain_expected_activities(self):
        """Test that expected activities are in the response"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Basketball",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        
        for activity in expected_activities:
            assert activity in activities


class TestSignupEndpoint:
    """Test the signup endpoint"""

    def test_signup_for_activity_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Basketball" in data["message"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        email = "newstudent@mergington.edu"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Tennis Club"]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/Tennis%20Club/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        new_count = len(response.json()["Tennis Club"]["participants"])
        assert new_count == initial_count + 1
        assert email in response.json()["Tennis Club"]["participants"]

    def test_signup_for_nonexistent_activity(self):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/NonexistentActivity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_duplicate_signup(self):
        """Test that we can't sign up twice for the same activity"""
        email = "duplicate@mergington.edu"
        activity = "Drama%20Club"
        
        # First signup should succeed
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()

    def test_signup_respects_max_participants(self):
        """Test that we can sign up up to max_participants"""
        activity = "Chess%20Club"
        
        # Get current participants and max
        response = client.get("/activities")
        chess_activity = response.json()["Chess Club"]
        current_count = len(chess_activity["participants"])
        max_participants = chess_activity["max_participants"]
        
        # Sign up remaining spots
        for i in range(max_participants - current_count):
            email = f"chessplayer{i}@mergington.edu"
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200


class TestUnregisterEndpoint:
    """Test the unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "unregister@mergington.edu"
        activity = "Programming%20Class"
        
        # Sign up first
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "removeme@mergington.edu"
        activity = "Art%20Studio"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify they're signed up
        response = client.get("/activities")
        assert email in response.json()["Art Studio"]["participants"]
        
        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Verify they're removed
        response = client.get("/activities")
        assert email not in response.json()["Art Studio"]["participants"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister from activity that doesn't exist"""
        response = client.post(
            "/activities/FakeActivity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_not_registered(self):
        """Test unregister when student is not registered"""
        response = client.post(
            "/activities/Debate%20Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
