"""Tests for Data Management API endpoints."""


class TestDataManagementApi:
    """Test export, import, and backup."""

    def test_export_empty(self, client):
        resp = client.get("/api/data/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"]["total_entries"] == 0
        assert "journal_entries" in data
        assert "habits" in data
        assert "goals" in data

    def test_export_with_data(self, client):
        # Create some data
        client.post("/api/journal", json={"content": "Test entry", "mood": 7})
        client.post("/api/habits", json={"habit_name": "Exercise"})
        client.post("/api/goals", json={"goal_title": "Learn Rust", "start_date": "2023-01-01"})

        resp = client.get("/api/data/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"]["total_entries"] == 1
        assert data["stats"]["total_habits"] == 1
        assert data["stats"]["total_goals"] == 1

    def test_import_data(self, client):
        import_payload = {
            "journal_entries": [
                {"content": "Imported entry 1", "entry_date": "2023-01-01"},
                {"content": "Imported entry 2", "entry_date": "2023-01-02"},
            ],
            "habits": [
                {"name": "Imported Habit"},
            ],
            "goals": [
                {"title": "Imported Goal", "start_date": "2023-01-01"},
            ],
        }
        resp = client.post("/api/data/import", json=import_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"]["entries"] == 2
        assert data["imported"]["habits"] == 1
        assert data["imported"]["goals"] == 1

    def test_list_backups(self, client):
        resp = client.get("/api/data/backup/list")
        assert resp.status_code == 200
        assert "backups" in resp.json()
