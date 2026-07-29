"""
Tests for the task API endpoints backing the TasksModal client component.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def reset_tasks():
    """Clear the session-scoped task store between tests.

    conftest builds the TestClient from a module-level app, so without this a
    POST in one test leaks into every later test and outcomes become
    order-dependent.
    """
    main.session_tasks.clear()
    main._task_seq = 0
    yield
    main.session_tasks.clear()
    main._task_seq = 0


def create_task(client, **overrides):
    payload = {"title": "Review Q4 stock levels", "priority": "high", "dueDate": "2025-10-08"}
    payload.update(overrides)
    return client.post("/api/tasks", json=payload)


class TestGetTasks:
    """Test suite for GET /api/tasks."""

    def test_returns_200_not_404(self, client):
        """The endpoint the client calls on mount must exist.

        This is the regression guard: App.vue calls getTasks() on every page
        load, so a missing route logged a 404 on every single navigation.
        """
        response = client.get("/api/tasks")
        assert response.status_code == 200

    def test_starts_empty(self, client):
        """A fresh server has no session tasks - the client falls back to mocks."""
        assert client.get("/api/tasks").json() == []

    def test_returns_newest_first(self, client):
        create_task(client, title="First")
        create_task(client, title="Second")

        titles = [task["title"] for task in client.get("/api/tasks").json()]
        assert titles == ["Second", "First"]


class TestCreateTask:
    """Test suite for POST /api/tasks."""

    def test_creates_task(self, client):
        response = create_task(client)
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Review Q4 stock levels"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-10-08"
        assert task["status"] == "pending"

    def test_uses_camel_case_due_date(self, client):
        """TasksModal.vue reads task.dueDate, so snake_case would render blank."""
        task = create_task(client).json()
        assert "dueDate" in task
        assert "due_date" not in task

    def test_id_cannot_collide_with_mock_task_ids(self, client):
        """useAuth.js mock tasks use integer ids 1-4 and are merged client-side.

        A numeric id here would make deleteTask() match the wrong task, because
        App.vue checks the mock list first.
        """
        task = create_task(client).json()
        assert isinstance(task["id"], str)
        assert task["id"] == "task-1"

    def test_ids_are_unique(self, client):
        first = create_task(client, title="A").json()
        second = create_task(client, title="B").json()
        assert first["id"] != second["id"]

    def test_defaults_priority_to_medium(self, client):
        response = client.post("/api/tasks", json={"title": "No priority", "dueDate": "2025-10-08"})
        assert response.json()["priority"] == "medium"

    def test_strips_whitespace_from_title(self, client):
        assert create_task(client, title="  Padded  ").json()["title"] == "Padded"

    def test_rejects_blank_title(self, client):
        assert create_task(client, title="   ").status_code == 400

    def test_rejects_unknown_priority(self, client):
        assert create_task(client, priority="urgent").status_code == 400

    def test_rejects_malformed_due_date(self, client):
        """formatDueDate() would render 'Invalid Date' for anything unparseable."""
        assert create_task(client, dueDate="08/10/2025").status_code == 400

    def test_rejects_missing_due_date(self, client):
        response = client.post("/api/tasks", json={"title": "No date"})
        assert response.status_code == 422


class TestToggleTask:
    """Test suite for PATCH /api/tasks/{task_id}."""

    def test_toggles_pending_to_completed(self, client):
        task_id = create_task(client).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_toggles_back_to_pending(self, client):
        task_id = create_task(client).json()["id"]

        client.patch(f"/api/tasks/{task_id}")
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "pending"

    def test_persists_in_list(self, client):
        task_id = create_task(client).json()["id"]
        client.patch(f"/api/tasks/{task_id}")

        assert client.get("/api/tasks").json()[0]["status"] == "completed"

    def test_unknown_task_returns_404(self, client):
        assert client.patch("/api/tasks/task-999").status_code == 404


class TestDeleteTask:
    """Test suite for DELETE /api/tasks/{task_id}."""

    def test_deletes_task(self, client):
        task_id = create_task(client).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert client.get("/api/tasks").json() == []

    def test_leaves_other_tasks_alone(self, client):
        keep = create_task(client, title="Keep").json()["id"]
        drop = create_task(client, title="Drop").json()["id"]

        client.delete(f"/api/tasks/{drop}")

        remaining = client.get("/api/tasks").json()
        assert [task["id"] for task in remaining] == [keep]

    def test_unknown_task_returns_404(self, client):
        assert client.delete("/api/tasks/task-999").status_code == 404

    def test_double_delete_returns_404(self, client):
        task_id = create_task(client).json()["id"]

        client.delete(f"/api/tasks/{task_id}")
        assert client.delete(f"/api/tasks/{task_id}").status_code == 404
