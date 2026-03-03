"""Tests for Journal API endpoints."""


class TestJournalApi:
    """Test journal CRUD operations."""

    def test_create_entry(self, client, auth_headers):
        resp = client.post("/api/journal", headers=auth_headers, json={
            "content": "Today was a great day. I felt productive and happy.",
            "mood": 8,
            "energy_level": 7,
            "stress_level": 3,
            "tags": ["productive", "happy"],
            "category": "daily",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "id" in data

    def test_list_entries(self, client, auth_headers):
        # Create two entries
        client.post("/api/journal", headers=auth_headers, json={"content": "Entry 1", "mood": 5})
        client.post("/api/journal", headers=auth_headers, json={"content": "Entry 2", "mood": 7})

        resp = client.get("/api/journal", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_get_entry_by_id(self, client, auth_headers):
        create_resp = client.post("/api/journal", headers=auth_headers, json={"content": "Test entry", "mood": 6})
        entry_id = create_resp.json()["id"]

        resp = client.get(f"/api/journal/{entry_id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "Test entry"
        assert data["mood"] == 6

    def test_update_entry(self, client, auth_headers):
        create_resp = client.post("/api/journal", headers=auth_headers, json={"content": "Original", "mood": 5})
        entry_id = create_resp.json()["id"]

        resp = client.put(f"/api/journal/{entry_id}", headers=auth_headers, json={"content": "Updated", "mood": 8})
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

        # Verify update
        get_resp = client.get(f"/api/journal/{entry_id}", headers=auth_headers)
        assert get_resp.json()["content"] == "Updated"
        assert get_resp.json()["mood"] == 8

    def test_delete_entry(self, client, auth_headers):
        create_resp = client.post("/api/journal", headers=auth_headers, json={"content": "To delete", "mood": 5})
        entry_id = create_resp.json()["id"]

        resp = client.delete(f"/api/journal/{entry_id}", headers=auth_headers)
        assert resp.status_code == 200

        # Verify deletion
        get_resp = client.get(f"/api/journal/{entry_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_get_nonexistent_entry(self, client, auth_headers):
        resp = client.get("/api/journal/99999", headers=auth_headers)
        assert resp.status_code == 404
