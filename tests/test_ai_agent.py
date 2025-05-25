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
    # Fallback should mark owner as None
    for res in results:
        assert res['owner'] is None


# Test when a request exception is raised

def test_identify_email_owners_exception(monkeypatch):
    monkeypatch.setattr(requests, 'post', dummy_exception_post)
    test_contexts = ['context X', 'context Y']
    os.environ['GPT4O_MINI_API_KEY'] = 'dummy_api_key'
    results = ai_agent.identify_email_owners(test_contexts)
    # In exception case, the entire list should be marked with owner as None
    for res in results:
        assert res['owner'] is None


# Test error when API key is not set

def test_identify_email_owners_missing_api_key(monkeypatch):
    if 'GPT4O_MINI_API_KEY' in os.environ:
        del os.environ['GPT4O_MINI_API_KEY']

    with pytest.raises(ValueError):
        ai_agent.identify_email_owners(['dummy context'])
