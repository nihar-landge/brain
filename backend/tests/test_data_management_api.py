"""Tests for Data Management API endpoints."""


class TestDataManagementApi:
    """Test export, import, and backup."""

    def test_export_empty(self, client, auth_headers):
        resp = client.get("/api/data/export", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"]["total_entries"] == 0
        assert "journal_entries" in data
        assert "habits" in data
        assert "goals" in data

        # Create some data
        client.post("/api/journal", headers=auth_headers, json={"content": "Test entry", "mood": 7})
        g = client.post("/api/goals", headers=auth_headers, json={"goal_title": "Learn Rust", "start_date": "2023-01-01"}).json()
        client.post("/api/habits", headers=auth_headers, json={"habit_name": "Exercise", "goal_id": g["id"]})

        resp = client.get("/api/data/export", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"]["total_entries"] == 1
        assert data["stats"]["total_habits"] == 1
        assert data["stats"]["total_goals"] == 1

    def test_import_data(self, client, auth_headers):
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
        resp = client.post("/api/data/import", headers=auth_headers, json=import_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"]["entries"] == 2
        assert data["imported"]["habits"] == 1
        assert data["imported"]["goals"] == 1

    def test_list_backups(self, client, auth_headers):
        resp = client.get("/api/data/backup/list", headers=auth_headers)
        assert resp.status_code == 200
        assert "backups" in resp.json()
