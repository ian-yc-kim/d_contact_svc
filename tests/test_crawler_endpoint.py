import pytest
from fastapi.testclient import TestClient

# The client fixture is provided in tests/conftest.py

def test_crawl_success(monkeypatch, client):
    # Monkey-patch crawl_website to return two HTML pages
    def fake_crawl(url: str):
        return ["<html>Email: test@example.com</html>", "<html>No email here</html>"]
    monkeypatch.setattr("d_contact_svc.routers.crawler.crawl_website", fake_crawl)

    # Monkey-patch extract_emails to extract email from HTML if present
    def fake_extract_emails(html: str):
        if "test@example.com" in html:
            return [{"email": "test@example.com", "context": "Email: test@example.com"}]
        return []
    monkeypatch.setattr("d_contact_svc.routers.crawler.extract_emails", fake_extract_emails)

    # Monkey-patch identify_email_owners to simulate owner identification based on the provided context
    def fake_identify_email_owners(contexts: list):
        results = []
        for ctx in contexts:
            results.append({"email_context": ctx, "owner": "Owner for " + ctx})
        return results
    monkeypatch.setattr("d_contact_svc.routers.crawler.identify_email_owners", fake_identify_email_owners)

    response = client.post("/crawl", json={"url": "http://example.com"})
    assert response.status_code == 200
    json_data = response.json()
    # Only the first HTML page returns an extracted email
    expected = {"results": [{"email": "test@example.com", "owner_name": "Owner for Email: test@example.com"}]}
    assert json_data == expected


def test_crawl_invalid_url(client):
    # Test that input validation rejects invalid URLs
    response = client.post("/crawl", json={"url": "invalid-url"})
    assert response.status_code == 422


def test_crawl_error(monkeypatch, client):
    # Simulate an exception in crawl_website
    def fake_crawl(url: str):
        raise Exception("Crawling error")
    monkeypatch.setattr("d_contact_svc.routers.crawler.crawl_website", fake_crawl)

    response = client.post("/crawl", json={"url": "http://example.com"})
    assert response.status_code == 500
    json_data = response.json()
    assert "detail" in json_data
    assert json_data["detail"] == "Failed to crawl website"
