import os
import json
import logging
import pytest
import requests

from d_contact_svc import ai_agent


class DummyResponse:
    def __init__(self, status_code, json_data=None, text=''):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        return self._json_data


def dummy_success_post(url, json, headers, timeout):
    # Simulate a successful API response
    # We'll assume that the API returns results in the same order as inputs
    email_contexts = json.get('email_contexts', [])
    results = []
    for ctx in email_contexts:
        # simple simulation: owner is a string 'owner_of_' + context
        results.append({"email_context": ctx, "owner": f"owner_of_{ctx}"})
    return DummyResponse(200, {"results": results})


def dummy_failure_post(url, json, headers, timeout):
    # Simulate a failed API response
    return DummyResponse(500, text='Internal Server Error')


def dummy_exception_post(url, json, headers, timeout):
    # Simulate a network exception
    raise requests.exceptions.Timeout('The request timed out')


def dummy_success_with_none_post(url, json, headers, timeout):
    # Simulate a successful API response where all owners are None to force regex fallback
    email_contexts = json.get('email_contexts', [])
    results = []
    for ctx in email_contexts:
        results.append({"email_context": ctx, "owner": None})
    return DummyResponse(200, {"results": results})


# Test when API returns a successful response

def test_identify_email_owners_success(monkeypatch):
    monkeypatch.setattr(requests, 'post', dummy_success_post)
    test_contexts = ['email context 1', 'email context 2', 'email context 3']
    os.environ['GPT4O_MINI_API_KEY'] = 'dummy_api_key'
    results = ai_agent.identify_email_owners(test_contexts)
    # Check that each result has the correct owner
    assert len(results) == len(test_contexts)
    for ctx, res in zip(test_contexts, results):
        assert res['email_context'] == ctx
        assert res['owner'] == f'owner_of_{ctx}'


# Test when API returns failure status code

def test_identify_email_owners_api_failure(monkeypatch):
    monkeypatch.setattr(requests, 'post', dummy_failure_post)
    test_contexts = ['email context A', 'email context B']
    os.environ['GPT4O_MINI_API_KEY'] = 'dummy_api_key'
    results = ai_agent.identify_email_owners(test_contexts)
    # Fallback should mark owner as None, then regex extraction is attempted
    # Since the email_context may not contain valid email, owner remains None
    for res in results:
        assert res['owner'] is None


# Test when a request exception is raised

def test_identify_email_owners_exception(monkeypatch):
    monkeypatch.setattr(requests, 'post', dummy_exception_post)
    test_contexts = ['context X', 'context Y']
    os.environ['GPT4O_MINI_API_KEY'] = 'dummy_api_key'
    results = ai_agent.identify_email_owners(test_contexts)
    # In exception case, the entire list should be marked with owner as None, then regex extraction runs
    for res in results:
        assert res['owner'] is None


# Test error when API key is not set

def test_identify_email_owners_missing_api_key(monkeypatch):
    if 'GPT4O_MINI_API_KEY' in os.environ:
        del os.environ['GPT4O_MINI_API_KEY']

    with pytest.raises(ValueError):
        ai_agent.identify_email_owners(['dummy context'])


# New test to verify regex extraction for email owner fallback

def test_identify_email_owners_regex_extraction(monkeypatch):
    # This dummy simulates a successful response where all owner fields are None to force regex fallback
    monkeypatch.setattr(requests, 'post', dummy_success_with_none_post)
    test_contexts = [
        'Please contact extracted_email: user@example.com for details.',
        'No valid email here in this context.',
        'Another context with extracted email: test.user+label@domain.co.uk found.'
    ]
    os.environ['GPT4O_MINI_API_KEY'] = 'dummy_api_key'
    results = ai_agent.identify_email_owners(test_contexts)

    # For the first and third contexts, even though API returned owner as None, regex should extract the email
    assert results[0]['owner'] == 'user@example.com'
    # For the second context, no valid email, so owner remains as None
    assert results[1]['owner'] is None
    assert results[2]['owner'] == 'test.user+label@domain.co.uk'
