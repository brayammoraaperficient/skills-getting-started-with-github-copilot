import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to a known state before each test"""
    from src.app import activities
    
    # Store original state
    original_state = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state
    for name, details in original_state.items():
        activities[name]["participants"] = details["participants"].copy()


class TestGetActivities:
    def test_get_all_activities(self, reset_activities):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_activity_structure(self, reset_activities):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupForActivity:
    def test_signup_new_participant(self, reset_activities):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_appears_in_activity(self, reset_activities):
        """Test that a signup is reflected in the activity"""
        email = "testuser@mergington.edu"
        
        # Signup
        response = client.post(
            f"/activities/Tennis Club/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify in activities list
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Tennis Club"]["participants"]
    
    def test_signup_duplicate_fails(self, reset_activities):
        """Test that signing up the same email twice fails"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Art Studio/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Art Studio/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_nonexistent_activity(self, reset_activities):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_multiple_activities(self, reset_activities):
        """Test that a student can sign up for multiple activities"""
        email = "multiactivity@mergington.edu"
        
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify in both activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]


class TestUnregisterFromActivity:
    def test_unregister_existing_participant(self, reset_activities):
        """Test unregistering an existing participant"""
        # First signup
        email = "toremove@mergington.edu"
        client.post(f"/activities/Debate Team/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Debate Team/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_removes_from_activity(self, reset_activities):
        """Test that unregistering removes the participant from the activity"""
        email = "testunregister@mergington.edu"
        
        # Signup
        client.post(f"/activities/Music Ensemble/signup?email={email}")
        
        # Verify they're in the activity
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Music Ensemble"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Music Ensemble/unregister?email={email}")
        
        # Verify they're removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Music Ensemble"]["participants"]
    
    def test_unregister_nonexistent_participant(self, reset_activities):
        """Test unregistering a participant who isn't signed up"""
        response = client.delete(
            "/activities/Science Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_nonexistent_activity(self, reset_activities):
        """Test unregistering from a non-existent activity"""
        response = client.delete(
            "/activities/Fake Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestEdgeCases:
    def test_special_characters_in_email(self, reset_activities):
        """Test handling emails with special characters"""
        email = "test+special@mergington.edu"
        response = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response.status_code == 200
    
    def test_activity_name_with_spaces(self, reset_activities):
        """Test activity names with spaces are handled correctly"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
