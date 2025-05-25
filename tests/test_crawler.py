import time
import logging
import requests
from urllib.robotparser import RobotFileParser
import pytest

from d_contact_svc import crawler

class DummyResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"Status code: {self.status_code}")


# Test helper: dummy HTML pages
HTML_PAGE_1 = "<html><body>Page 1 <a href='page2.html'>next</a></body></html>"
HTML_PAGE_2 = "<html><body>Page 2 <a href='page1.html'>prev</a></body></html>"
HTML_PAGE_DISALLOWED = "<html><body>You should not see me</body></html>"


def fake_requests_get(url, timeout):
    # Simulate behavior based on URL
    if "invalid" in url:
        raise requests.RequestException('Invalid URL')
    if url.endswith("page1.html"):
        return DummyResponse(HTML_PAGE_1)
    if url.endswith("page2.html"):
        return DummyResponse(HTML_PAGE_2)
    return DummyResponse(HTML_PAGE_1)


class DummyRobotFileParser:
    def __init__(self, disallowed_urls=None):
        self.disallowed_urls = disallowed_urls or []

    def set_url(self, url):
        pass

    def read(self):
        pass

    def can_fetch(self, useragent, url):
        # Disallow crawling for any URL in the disallowed list
        for disallowed in self.disallowed_urls:
            if disallowed in url:
                return False
        return True


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    # Patch requests.get to use fake_requests_get
    monkeypatch.setattr(requests, "get", fake_requests_get)
    # Patch RobotFileParser to use DummyRobotFileParser without restrictions by default
    monkeypatch.setattr(crawler, "RobotFileParser", lambda: DummyRobotFileParser())


def test_duplicate_pages(monkeypatch):
    # Test to ensure duplicate pages are not crawled
    start_url = "http://example.com/page1.html"
    results = crawler.crawl_website(start_url)
    # Both page1 and page2 are linked; even though they refer to each other,
    # the crawler should avoid infinite loops and duplicates
    assert len(results) == 2


def test_robots_txt_disallow(monkeypatch):
    # Test to check that URLs disallowed by robots.txt are skipped
    def fake_rp():
        return DummyRobotFileParser(disallowed_urls=["/forbidden.html"])
    monkeypatch.setattr(crawler, "RobotFileParser", lambda: fake_rp())

    def fake_requests_get2(url, timeout):
        if "forbidden.html" in url:
            return DummyResponse(HTML_PAGE_DISALLOWED)
        return DummyResponse(HTML_PAGE_1)
    monkeypatch.setattr(requests, "get", fake_requests_get2)

    start_url = "http://example.com/forbidden.html"
    results = crawler.crawl_website(start_url)
    # Since the URL is disallowed, it should not be fetched and result should be empty
    assert len(results) == 0


def test_invalid_url(monkeypatch):
    # Test to handle invalid URLs gracefully
    start_url = "http://invalid-url"
    results = crawler.crawl_website(start_url)
    # On exception, the result list should be empty
    assert results == []


def test_global_timeout(monkeypatch):
    # Test global timeout enforcement
    # Monkeypatch time.time to simulate a timeout scenario
    original_time = time.time()
    times = [original_time, original_time + 1801]  # Immediately exceed global timeout after first call
    def fake_time():
        return times.pop(0) if times else original_time + 1801
    monkeypatch.setattr(time, "time", fake_time)

    start_url = "http://example.com/page1.html"
    results = crawler.crawl_website(start_url)
    # With global timeout reached, crawler should break early
    # Depending on execution, it may have 0 or 1 page fetched
    assert len(results) <= 1
