"""
Tests for Tasks API — CRUD operations.
"""

import pytest


class TestTasksApi:
    """Task endpoint tests."""

    def test_create_task(self, client, auth_headers):
        """Create a new task."""
        resp = client.post("/api/tasks", headers=auth_headers, json={
            "title": "Write unit tests",
            "priority": "high",
            "status": "todo",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "id" in data

    def test_get_tasks(self, client, auth_headers):
        """List tasks."""
        client.post("/api/tasks", headers=auth_headers, json={
            "title": "Task A",
        })
        client.post("/api/tasks", headers=auth_headers, json={
            "title": "Task B",
        })
        resp = client.get("/api/tasks", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2

    def test_get_single_task(self, client, auth_headers):
        """Get a specific task by ID."""
        create = client.post("/api/tasks", headers=auth_headers, json={
            "title": "Specific task",
        })
        task_id = create.json()["id"]
        resp = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Specific task"

    def test_update_task(self, client, auth_headers):
        """Update an existing task."""
        create = client.post("/api/tasks", headers=auth_headers, json={
            "title": "Old title",
        })
        task_id = create.json()["id"]
        resp = client.put(f"/api/tasks/{task_id}", headers=auth_headers, json={
            "title": "New title",
            "status": "in_progress",
        })
        assert resp.status_code == 200

    def test_delete_task(self, client, auth_headers):
        """Delete a task."""
        create = client.post("/api/tasks", headers=auth_headers, json={
            "title": "To delete",
        })
        task_id = create.json()["id"]
        resp = client.delete(f"/api/tasks/{task_id}", headers=auth_headers)
        assert resp.status_code == 200

        # Verify it's gone
        resp = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_create_task_with_goal_link(self, client, auth_headers, test_goal):
        """Create a task linked to a goal."""
        resp = client.post("/api/tasks", headers=auth_headers, json={
            "title": "Goal-linked task",
            "goal_id": test_goal,
        })
        assert resp.status_code == 200
