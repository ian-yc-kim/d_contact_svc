import re
import logging
import pytest
from d_contact_svc.email_extractor import extract_emails


def test_standard_email_extraction():
    # Test extraction of standard email formats
    html = "Hello, please contact us at user@example.com for details."
    results = extract_emails(html)
    assert any('user@example.com' == entry['email'] for entry in results), "Standard email not found"
    for entry in results:
        if entry['email'] == 'user@example.com':
            # Ensure context contains at least part of surrounding text
            assert 'user@example.com' in entry['context']
            break


def test_obfuscated_email_extraction():
    # Test extraction of obfuscated emails
    html = "For support, email admin [at] example.com immediately."
    results = extract_emails(html)
    # The obfuscated email should be converted to standard format
    assert any('admin@example.com' == entry['email'] for entry in results), "Obfuscated email not correctly converted"


def test_context_extraction_boundaries():
    # Test extraction when email is near the beginning or end of the string
    html_start = "user@example.com is our contact at the beginning."
    results_start = extract_emails(html_start)
    for entry in results_start:
        if entry['email'] == 'user@example.com':
            # Since it is at the beginning, context might be less than 20 characters before email
            assert entry['context'].startswith('user@example.com') or 'user@example.com' in entry['context']

    html_end = "Our contact is at the end: user@example.com"
    results_end = extract_emails(html_end)
    for entry in results_end:
        if entry['email'] == 'user@example.com':
            # Since it is at the end, context might be less than 20 characters after email
            assert entry['context'].endswith('user@example.com') or 'user@example.com' in entry['context']


def test_no_email_found():
    # Test with HTML input that contains no email addresses
    html = "This content has no emails."
    results = extract_emails(html)
    assert results == [], "Should return an empty list when no emails are found"


def test_non_string_input(capfd):
    # Test for non-string input, function should handle it and return empty list
    # Since logging is used, we won't get an exception but an empty list
    result = extract_emails(12345)  # non-string input
    assert result == [], "Should return empty list for non-string input"

# Additional edge case: multiple emails including both formats

def test_multiple_emails_extraction():
    html = (
        "Contact us at first.user@example.com or reach support at second.user [at] example.org. "
        "Also, inform admin [at] example.net for overall inquiries."
    )
    results = extract_emails(html)
    extracted_emails = {entry['email'] for entry in results}
    expected_emails = {"first.user@example.com", "second.user@example.org", "admin@example.net"}
    assert extracted_emails == expected_emails, "Multiple emails not correctly extracted"
