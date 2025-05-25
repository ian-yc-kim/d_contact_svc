import re
import logging
from typing import List, Dict


def extract_emails(html: str) -> List[Dict[str, str]]:
    """
    Extracts email addresses and their surrounding context from the provided HTML content.

    The function searches for both standard email formats (e.g., user@domain.com)
    and common obfuscated formats (e.g., user [at] domain.com), extracting at least
    20 characters of context before and after each found email address.

    :param html: The HTML content as a string.
    :return: A list of dictionaries with keys 'email' and 'context'.
    """
    results: List[Dict[str, str]] = []
    try:
        if not isinstance(html, str):
            raise ValueError('Input must be a string')

        # Define regex patterns for standard and obfuscated emails
        # Standard email pattern: e.g., user@domain.com
        standard_email_pattern = r'(?P<email>[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})'
        # Obfuscated email pattern: e.g., user [at] domain.com (allow optional spaces)
        obfuscated_email_pattern = r'(?P<email>[A-Za-z0-9._%+-]+\s*\[\s*at\s*\]\s*[A-Za-z0-9.-]+\.[A-Za-z]{2,})'

        # Function to extract context given a match object
        def get_context(match):
            start, end = match.span()
            # Calculate context boundaries ensuring not to exceed string limits
            context_start = max(0, start - 20)
            context_end = min(len(html), end + 20)
            return html[context_start:context_end]

        # Process standard emails
        for match in re.finditer(standard_email_pattern, html):
            email = match.group('email')
            context = get_context(match)
            results.append({'email': email, 'context': context})

        # Process obfuscated emails
        for match in re.finditer(obfuscated_email_pattern, html):
            raw_email = match.group('email')
            # Replace obfuscation to standard format
            email = re.sub(r'\s*\[\s*at\s*\]\s*', '@', raw_email)
            context = get_context(match)
            results.append({'email': email, 'context': context})

        return results

    except Exception as e:
        logging.error(e, exc_info=True)
        # If input is invalid or another error occurred, return empty list
        return []

# Example usage inline comments:
# html_content = "<p>Contact us at user@example.com for more info.</p>"
# emails = extract_emails(html_content)
# print(emails)
