import pytest

# Test client is provided by conftest.py

def test_identify_email_owner_valid(client, monkeypatch):
    # Monkey patch the identify_email_owners function to simulate success
    def fake_identify_email_owners(email_contexts):
        return [{"email_context": ctx, "owner": f"owner_" + ctx} for ctx in email_contexts]

    monkeypatch.setattr("d_contact_svc.routers.ai_agent_endpoint.identify_email_owners", fake_identify_email_owners)
    payload = {"email_contexts": ["user1@example.com", "user2@example.com"]}
    response = client.post("/identify-email-owner", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["results"] == [
        {"email_context": "user1@example.com", "owner": "owner_user1@example.com"},
        {"email_context": "user2@example.com", "owner": "owner_user2@example.com"}
    ]


def test_identify_email_owner_invalid_payload(client):
    # Send an invalid payload where email_contexts is not a list
    payload = {"email_contexts": "not a list"}
    response = client.post("/identify-email-owner", json=payload)
    # FastAPI returns 422 Unprocessable Entity for validation errors
    assert response.status_code == 422


def test_identify_email_owner_internal_error(client, monkeypatch):
    # Simulate an internal error in the identify_email_owners function
    def fake_identify_email_owners(email_contexts):
        raise Exception("Simulated failure")
    monkeypatch.setattr("d_contact_svc.routers.ai_agent_endpoint.identify_email_owners", fake_identify_email_owners)
    payload = {"email_contexts": ["user@example.com"]}
    response = client.post("/identify-email-owner", json=payload)
    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "Internal Server Error"
