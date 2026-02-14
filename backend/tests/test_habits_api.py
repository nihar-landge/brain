"""Tests for Habits API endpoints."""


class TestHabitsApi:
    """Test habit CRUD, logging, and stats."""

    def test_create_habit(self, client):
        resp = client.post("/api/habits", json={
            "habit_name": "Morning Meditation",
            "habit_description": "10 min meditation",
            "habit_category": "mindfulness",
            "target_frequency": "daily",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "id" in data

    def test_list_habits(self, client):
        client.post("/api/habits", json={"habit_name": "Exercise"})
        client.post("/api/habits", json={"habit_name": "Read"})

        resp = client.get("/api/habits")
        assert resp.status_code == 200
        habits = resp.json()
        assert len(habits) == 2

    def test_get_habit(self, client):
        create = client.post("/api/habits", json={"habit_name": "Yoga"})
        hid = create.json()["id"]

        resp = client.get(f"/api/habits/{hid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Yoga"

    def test_update_habit(self, client):
        create = client.post("/api/habits", json={"habit_name": "Walk"})
        hid = create.json()["id"]

        resp = client.put(f"/api/habits/{hid}", json={"habit_name": "Long Walk"})
        assert resp.status_code == 200

    def test_delete_habit(self, client):
        create = client.post("/api/habits", json={"habit_name": "Temp"})
        hid = create.json()["id"]

        resp = client.delete(f"/api/habits/{hid}")
        assert resp.status_code == 200

        # Should be gone
        get_resp = client.get(f"/api/habits/{hid}")
        assert get_resp.status_code == 404

    def test_log_habit(self, client):
        create = client.post("/api/habits", json={"habit_name": "Run"})
        hid = create.json()["id"]

        resp = client.post(f"/api/habits/{hid}/log", json={
            "completed": True,
            "difficulty": 3,
            "satisfaction": 4,
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_log_habit_idempotent(self, client):
        """Logging the same habit twice on same day should update, not duplicate."""
        create = client.post("/api/habits", json={"habit_name": "Stretch"})
        hid = create.json()["id"]

        client.post(f"/api/habits/{hid}/log", json={"completed": True})
        resp = client.post(f"/api/habits/{hid}/log", json={"completed": False})
        assert resp.status_code == 200
        assert "updated" in resp.json()["message"].lower()

    def test_habit_stats(self, client):
        create = client.post("/api/habits", json={"habit_name": "Code"})
        hid = create.json()["id"]

        # Log completion
        client.post(f"/api/habits/{hid}/log", json={"completed": True})

        resp = client.get(f"/api/habits/{hid}/stats")
        assert resp.status_code == 200
        stats = resp.json()
        assert stats["total_logs"] == 1
        assert stats["total_completed"] == 1

    def test_habit_not_found(self, client):
        resp = client.get("/api/habits/99999")
        assert resp.status_code == 404
