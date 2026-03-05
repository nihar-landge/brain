"""
Tests for Dopamine Menu API — CRUD for items and events.
"""

import pytest


class TestDopamineApi:
    """Dopamine endpoint tests."""

    def test_get_items_seeds_defaults(self, client, auth_headers):
        """First GET should seed default dopamine items."""
        resp = client.get("/api/dopamine/items", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # Default items should be auto-seeded
        assert len(data) > 0

    def test_create_item(self, client, auth_headers):
        """Create a custom dopamine item."""
        resp = client.post("/api/dopamine/items", headers=auth_headers, json={
            "category": "starter",
            "title": "3 deep breaths",
            "duration_min": 2,
            "energy_type": "relax",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "id" in data

    def test_update_item(self, client, auth_headers):
        """Update a dopamine item."""
        create = client.post("/api/dopamine/items", headers=auth_headers, json={
            "category": "main",
            "title": "Walk outside",
            "duration_min": 15,
        })
        item_id = create.json()["id"]

        resp = client.put(f"/api/dopamine/items/{item_id}", headers=auth_headers, json={
            "title": "Walk in park",
            "duration_min": 20,
        })
        assert resp.status_code == 200

    def test_delete_item(self, client, auth_headers):
        """Delete a dopamine item."""
        create = client.post("/api/dopamine/items", headers=auth_headers, json={
            "category": "dessert",
            "title": "Watch funny video",
        })
        item_id = create.json()["id"]

        resp = client.delete(f"/api/dopamine/items/{item_id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_create_event(self, client, auth_headers):
        """Create a dopamine event log."""
        resp = client.post("/api/dopamine/events", headers=auth_headers, json={
            "trigger_type": "manual",
            "accepted": True,
            "completed": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data

    def test_update_event(self, client, auth_headers):
        """Update a dopamine event (mark completed)."""
        create = client.post("/api/dopamine/events", headers=auth_headers, json={
            "trigger_type": "long_session",
            "accepted": True,
        })
        event_id = create.json()["id"]

        resp = client.put(f"/api/dopamine/events/{event_id}", headers=auth_headers, json={
            "completed": True,
        })
        assert resp.status_code == 200
