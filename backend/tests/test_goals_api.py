"""Tests for Goals API endpoints."""


class TestGoalsApi:
    """Test goal CRUD operations."""

    def test_create_goal(self, client):
        resp = client.post("/api/goals", json={
            "goal_title": "Learn Python",
            "goal_description": "Complete a Python course",
            "goal_category": "learning",
            "start_date": "2023-01-01",
            "priority": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "id" in data

    def test_list_goals(self, client):
        client.post("/api/goals", json={"goal_title": "Goal A", "start_date": "2023-01-01"})
        client.post("/api/goals", json={"goal_title": "Goal B", "start_date": "2023-01-02"})

        resp = client.get("/api/goals")
        assert resp.status_code == 200
        goals = resp.json()
        assert len(goals) == 2

    def test_get_goal(self, client):
        create = client.post("/api/goals", json={"goal_title": "Fitness", "start_date": "2023-01-01"})
        gid = create.json()["id"]

        resp = client.get(f"/api/goals/{gid}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Fitness"

    def test_update_goal(self, client):
        create = client.post("/api/goals", json={"goal_title": "Old Title", "start_date": "2023-01-01"})
        gid = create.json()["id"]

        resp = client.put(f"/api/goals/{gid}", json={"goal_title": "New Title"})
        assert resp.status_code == 200

    def test_delete_goal(self, client):
        create = client.post("/api/goals", json={"goal_title": "Temp Goal", "start_date": "2023-01-01"})
        gid = create.json()["id"]

        resp = client.delete(f"/api/goals/{gid}")
        assert resp.status_code == 200

        get_resp = client.get(f"/api/goals/{gid}")
        assert get_resp.status_code == 404

    def test_goal_not_found(self, client):
        resp = client.get("/api/goals/99999")
        assert resp.status_code == 404
