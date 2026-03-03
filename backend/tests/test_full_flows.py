"""Integration tests for full user flows."""


class TestFullFlows:
    """Test end-to-end workflows across multiple APIs."""

    def test_journal_export_flow(self, client, auth_headers):
        """Create journal entries then export and verify they're included."""
        # Create entries
        client.post("/api/journal", headers=auth_headers, json={"content": "Day 1 - Feeling great", "mood": 8})
        client.post("/api/journal", headers=auth_headers, json={"content": "Day 2 - Stressed", "mood": 4})

        # Export
        export = client.get("/api/data/export", headers=auth_headers).json()
        assert export["stats"]["total_entries"] == 2
        contents = [e["content"] for e in export["journal_entries"]]
        assert "Day 1 - Feeling great" in contents
        assert "Day 2 - Stressed" in contents

    def test_habit_log_stats_flow(self, client, auth_headers):
        """Create habit, log it, then verify stats reflect the log."""
        # Create Goal first
        g = client.post("/api/goals", headers=auth_headers, json={"goal_title": "Health", "start_date": "2023-01-01"}).json()
        
        # Create Habit
        create = client.post("/api/habits", headers=auth_headers, json={"habit_name": "Water", "goal_id": g["id"]})
        hid = create.json()["id"]

        # Log
        client.post(f"/api/habits/{hid}/log", headers=auth_headers, json={"completed": True, "difficulty": 2})

        # Stats
        stats = client.get(f"/api/habits/{hid}/stats", headers=auth_headers).json()
        assert stats["total_logs"] == 1
        assert stats["total_completed"] == 1
        assert stats["completion_rate"] == 1.0

    def test_goal_crud_flow(self, client, auth_headers):
        """Create, update progress, list, and delete a goal."""
        # Create
        create = client.post("/api/goals", headers=auth_headers, json={
            "goal_title": "Ship v2",
            "goal_category": "work",
            "start_date": "2023-01-01",
            "priority": 5,
        })
        gid = create.json()["id"]

        # Update
        client.put(f"/api/goals/{gid}", headers=auth_headers, json={"progress": 50})

        # List — should be there
        goals = client.get("/api/goals", headers=auth_headers).json()
        assert any(g["id"] == gid for g in goals)

        # Delete
        client.delete(f"/api/goals/{gid}", headers=auth_headers)
        assert client.get(f"/api/goals/{gid}", headers=auth_headers).status_code == 404

    def test_system_endpoints(self, client, auth_headers):
        """Health and stats endpoints should always work."""
        health = client.get("/api/health", headers=auth_headers)
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"

        stats = client.get("/api/stats", headers=auth_headers)
        assert stats.status_code == 200
        assert "total_journal_entries" in stats.json()

    def test_chat_clear_flow(self, client, auth_headers):
        """Clear chat should succeed even when empty."""
        resp = client.delete("/api/chat/clear", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
