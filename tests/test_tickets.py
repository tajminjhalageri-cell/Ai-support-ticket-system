from app.core.config import settings


def create_ticket(client, title="Cannot sign in", **overrides):
    payload = {
        "title": title,
        "description": "The sign-in page rejects my credentials.",
        **overrides,
    }
    return client.post("/api/v1/tickets", json=payload)


def test_create_and_retrieve_ticket(client):
    created = create_ticket(client)

    assert created.status_code == 201
    ticket = created.json()
    assert ticket["title"] == "Cannot sign in"
    assert ticket["status"] == "open"
    assert ticket["priority"] == "medium"
    assert ticket["created_at"]
    assert client.get(f"/api/v1/tickets/{ticket['id']}").json() == ticket


def test_list_search_filters_sort_and_pagination(client):
    create_ticket(client, "Billing question", priority="low")
    create_ticket(client, "Sign-in issue", priority="high", status="in_progress")
    create_ticket(client, "Another billing issue", priority="critical")

    response = client.get(
        "/api/v1/tickets",
        params={
            "q": "billing",
            "sort_by": "title",
            "sort_order": "asc",
            "skip": 0,
            "limit": 1,
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 2
    assert len(result["items"]) == 1
    assert result["items"][0]["title"] == "Another billing issue"
    assert result["skip"] == 0
    assert result["limit"] == 1
    priority_result = client.get(
        "/api/v1/tickets", params={"priority": "critical"}
    ).json()
    assert priority_result["total"] == 1
    assert priority_result["items"][0]["title"] == "Another billing issue"


def test_status_filter_and_pagination(client):
    create_ticket(client, "First", status="open")
    create_ticket(client, "Second", status="closed")
    create_ticket(client, "Third", status="closed")

    response = client.get(
        "/api/v1/tickets", params={"status": "closed", "skip": 1, "limit": 1}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["status"] == "closed"


def test_update_ticket_and_reject_empty_update(client):
    ticket_id = create_ticket(client).json()["id"]

    updated = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "resolved", "priority": "high"},
    )
    empty_update = client.patch(f"/api/v1/tickets/{ticket_id}", json={})

    assert updated.status_code == 200
    assert updated.json()["status"] == "resolved"
    assert updated.json()["priority"] == "high"
    assert updated.json()["title"] == "Cannot sign in"
    assert (
        updated.json()["description"]
        == "The sign-in page rejects my credentials."
    )
    assert empty_update.status_code == 422


def test_invalid_create_and_invalid_update_return_validation_errors(client):
    invalid_create = client.post(
        "/api/v1/tickets", json={"title": "x", "description": ""}
    )
    ticket_id = create_ticket(client).json()["id"]
    invalid_update = client.patch(
        f"/api/v1/tickets/{ticket_id}", json={"status": "not-a-status"}
    )

    assert invalid_create.status_code == 422
    assert invalid_update.status_code == 422


def test_unknown_input_fields_are_rejected(client):
    response = create_ticket(client, unexpected="not accepted")

    assert response.status_code == 422


def test_missing_ticket_returns_not_found(client):
    assert client.get("/api/v1/tickets/999").status_code == 404
    assert client.patch("/api/v1/tickets/999", json={"status": "closed"}).status_code == 404


def test_local_frontend_can_use_ticket_api(client):
    response = client.options(
        "/api/v1/tickets/1",
        headers={
            "Origin": "http://127.0.0.1:5500",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"
    assert "PATCH" in response.headers["access-control-allow-methods"]


def test_delete_requires_configured_key_and_removes_ticket(client, monkeypatch):
    ticket_id = create_ticket(client).json()["id"]
    monkeypatch.setattr(settings, "ticket_delete_api_key", None)
    assert client.delete(f"/api/v1/tickets/{ticket_id}").status_code == 503

    monkeypatch.setattr(settings, "ticket_delete_api_key", "test-delete-key")
    assert (
        client.delete(
            f"/api/v1/tickets/{ticket_id}",
            headers={"X-Delete-API-Key": "wrong-key"},
        ).status_code
        == 403
    )
    deleted = client.delete(
        f"/api/v1/tickets/{ticket_id}",
        headers={"X-Delete-API-Key": "test-delete-key"},
    )

    assert deleted.status_code == 204
    assert client.get(f"/api/v1/tickets/{ticket_id}").status_code == 404
