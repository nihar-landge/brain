"""Tests for Habits API endpoints."""


class TestHabitsApi:
    """Test habit CRUD, logging, and stats."""

    def test_create_habit(self, client, auth_headers, test_goal):
        resp = client.post("/api/habits", headers=auth_headers, json={
            "habit_name": "Morning Meditation",
            "habit_description": "10 min meditation",
            "habit_category": "mindfulness",
            "target_frequency": "daily",
            "goal_id": test_goal
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "id" in data

    def test_list_habits(self, client, auth_headers, test_goal):
        client.post("/api/habits", headers=auth_headers, json={"habit_name": "Exercise", "goal_id": test_goal})
        client.post("/api/habits", headers=auth_headers, json={"habit_name": "Read", "goal_id": test_goal})

        resp = client.get("/api/habits", headers=auth_headers)
        assert resp.status_code == 200
        habits = resp.json()
        assert len(habits) == 2

    def test_get_habit(self, client, auth_headers, test_goal):
        create = client.post("/api/habits", headers=auth_headers, json={"habit_name": "Yoga", "goal_id": test_goal})
        hid = create.json()["id"]

        resp = client.get(f"/api/habits/{hid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Yoga"

    def test_update_habit(self, client, auth_headers, test_goal):
        create = client.post("/api/habits", headers=auth_headers, json={"habit_name": "Walk", "goal_id": test_goal})
        hid = create.json()["id"]

        resp = client.put(f"/api/habits/{hid}", headers=auth_headers, json={"habit_name": "Long Walk"})
        assert resp.status_code == 200

    def test_delete_habit(self, client, auth_headers, test_goal):
        create = client.post("/api/habits", headers=auth_headers, json={"habit_name": "Temp", "goal_id": test_goal})
        hid = create.json()["id"]

        resp = client.delete(f"/api/habits/{hid}", headers=auth_headers)
        assert resp.status_code == 200

        # Should be gone
        get_resp = client.get(f"/api/habits/{hid}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_log_habit(self, client, auth_headers, test_goal):
        create = client.post("/api/habits", headers=auth_headers, json={"habit_name": "Run", "goal_id": test_goal})
        hid = create.json()["id"]

        resp = client.post(f"/api/habits/{hid}/log", headers=auth_headers, json={
            "completed": True,
            "difficulty": 3,
            "satisfaction": 4,
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_log_habit_idempotent(self, client, auth_headers, test_goal):
        """Logging the same habit twice on same day should update, not duplicate."""
        create = client.post("/api/habits", headers=auth_headers, json={"habit_name": "Stretch", "goal_id": test_goal})
        hid = create.json()["id"]

        client.post(f"/api/habits/{hid}/log", headers=auth_headers, json={"completed": True})
        resp = client.post(f"/api/habits/{hid}/log", headers=auth_headers, json={"completed": False})
        assert resp.status_code == 200
        assert "updated" in resp.json()["message"].lower()

    def test_habit_stats(self, client, auth_headers, test_goal):
        create = client.post("/api/habits", headers=auth_headers, json={"habit_name": "Code", "goal_id": test_goal})
        hid = create.json()["id"]

        # Log completion
        client.post(f"/api/habits/{hid}/log", headers=auth_headers, json={"completed": True})

        resp = client.get(f"/api/habits/{hid}/stats", headers=auth_headers)
        assert resp.status_code == 200
        stats = resp.json()
        assert stats["total_logs"] == 1
        assert stats["total_completed"] == 1

    def test_habit_not_found(self, client, auth_headers):
        resp = client.get("/api/habits/99999", headers=auth_headers)
        assert resp.status_code == 404
