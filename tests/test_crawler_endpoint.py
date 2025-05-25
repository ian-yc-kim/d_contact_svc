import pytest
from fastapi.testclient import TestClient

# The client fixture is provided in tests/conftest.py

def test_crawl_success(monkeypatch, client):
    # Monkey-patch the crawl_website function for a successful response
    def fake_crawl(url: str):
        return ["<html>Page1</html>", "<html>Page2</html>"]

    monkeypatch.setattr("d_contact_svc.routers.crawler.crawl_website", fake_crawl)
    response = client.post("/crawl", json={"url": "http://example.com"})
    assert response.status_code == 200
    json_data = response.json()
    assert "results" in json_data
    assert json_data["results"] == ["<html>Page1</html>", "<html>Page2</html>"]


def test_crawl_invalid_url(client):
    # Test invalid URL input; HttpUrl validation should trigger a 422 error
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
