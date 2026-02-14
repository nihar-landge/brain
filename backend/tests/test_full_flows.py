"""Integration tests for full user flows."""


class TestFullFlows:
    """Test end-to-end workflows across multiple APIs."""

    def test_journal_export_flow(self, client):
        """Create journal entries then export and verify they're included."""
        # Create entries
        client.post("/api/journal", json={"content": "Day 1 - Feeling great", "mood": 8})
        client.post("/api/journal", json={"content": "Day 2 - Stressed", "mood": 4})

        # Export
        export = client.get("/api/data/export").json()
        assert export["stats"]["total_entries"] == 2
        contents = [e["content"] for e in export["journal_entries"]]
        assert "Day 1 - Feeling great" in contents
        assert "Day 2 - Stressed" in contents

    def test_habit_log_stats_flow(self, client):
        """Create habit, log it, then verify stats reflect the log."""
        # Create
        create = client.post("/api/habits", json={"habit_name": "Water"})
        hid = create.json()["id"]

        # Log
        client.post(f"/api/habits/{hid}/log", json={"completed": True, "difficulty": 2})

        # Stats
        stats = client.get(f"/api/habits/{hid}/stats").json()
        assert stats["total_logs"] == 1
        assert stats["total_completed"] == 1
        assert stats["completion_rate"] == 1.0

    def test_goal_crud_flow(self, client):
        """Create, update progress, list, and delete a goal."""
        # Create
        create = client.post("/api/goals", json={
            "goal_title": "Ship v2",
            "goal_category": "work",
            "start_date": "2023-01-01",
            "priority": 5,
        })
        gid = create.json()["id"]

        # Update
        client.put(f"/api/goals/{gid}", json={"progress": 50})

        # List — should be there
        goals = client.get("/api/goals").json()
        assert any(g["id"] == gid for g in goals)

        # Delete
        client.delete(f"/api/goals/{gid}")
        assert client.get(f"/api/goals/{gid}").status_code == 404

    def test_system_endpoints(self, client):
        """Health and stats endpoints should always work."""
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"

        stats = client.get("/api/stats")
        assert stats.status_code == 200
        assert "total_journal_entries" in stats.json()

    def test_chat_clear_flow(self, client):
        """Clear chat should succeed even when empty."""
        resp = client.delete("/api/chat/clear")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
