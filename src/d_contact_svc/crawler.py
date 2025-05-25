import logging
import time
from typing import List, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup


def crawl_website(url: str) -> List[str]:
    """
    Crawls the website starting from the given URL.
    Retrieves HTML content from pages, extracts links, respects robots.txt rules,
    handles pagination by following 'next' links, and avoids duplicate crawling.

    Args:
        url (str): The starting URL for crawling.

    Returns:
        List[str]: A list of HTML content strings from the crawled pages.
    """
    start_time = time.time()
    global_timeout = 1800  # 30 minutes in seconds
    visited: Set[str] = set()
    html_contents: List[str] = []
    to_visit = [url]

    # Prepare robots.txt parser
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = urljoin(base_url, "robots.txt")
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
    except Exception as e:
        logging.error(e, exc_info=True)
        # If robots.txt cannot be fetched, assume allow crawling
        rp = None

    while to_visit:
        # Enforce global timeout
        if time.time() - start_time > global_timeout:
            logging.error("Global timeout reached. Stopping crawler.")
            break

        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        # Check robots.txt if available
        if rp and not rp.can_fetch("*", current_url):
            logging.info(f"Disallowed by robots.txt: {current_url}")
            visited.add(current_url)
            continue

        try:
            response = requests.get(current_url, timeout=10)
            response.raise_for_status()
            html = response.text
            html_contents.append(html)
            visited.add(current_url)

            soup = BeautifulSoup(html, "html.parser")
            # Extract all links from <a> tags
            for link in soup.find_all("a", href=True):
                href = link['href']
                full_url = urljoin(current_url, href)
                if full_url in visited or full_url in to_visit:
                    continue
                # Check for pagination hints: link text containing 'next' or rel attribute
                if 'next' in link.text.lower() or ('rel' in link.attrs and 'next' in link.attrs['rel']):
                    to_visit.append(full_url)
                else:
                    to_visit.append(full_url)
        except Exception as e:
            logging.error(e, exc_info=True)
            visited.add(current_url)

    return html_contents
