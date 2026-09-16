"""Unit tests for ai_client.py's AI_PROVIDER=depot path — no network, no Flask app needed, just
the module's own dispatch and its httpx call shape."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
import pytest

import ai_client


def test_depot_is_a_configured_provider(monkeypatch):
    monkeypatch.setattr(ai_client, "AI_PROVIDER", "depot")
    assert ai_client.is_configured() is True


def test_chat_dispatches_to_the_depot_proxy(monkeypatch):
    monkeypatch.setattr(ai_client, "AI_PROVIDER", "depot")
    seen = {}

    def fake_post(url, json, timeout):
        seen["url"] = url
        seen["json"] = json
        return httpx.Response(200, json={"reply": "hello from the depot"}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    reply = ai_client.chat([{"role": "user", "content": "hi"}], system="be nice")

    assert reply == "hello from the depot"
    assert seen["url"] == "http://localhost:8090/api/ai/chat"
    assert seen["json"] == {"messages": [{"role": "user", "content": "hi"}], "system": "be nice", "max_tokens": 1024}


def test_chat_surfaces_a_not_configured_error_from_the_proxy(monkeypatch):
    monkeypatch.setattr(ai_client, "AI_PROVIDER", "depot")

    def fake_post(url, json, timeout):
        return httpx.Response(200, json={"error": "AI is not configured for this instance."}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    reply = ai_client.chat([{"role": "user", "content": "hi"}])
    assert "AI is not configured" in reply


def test_chat_degrades_when_the_depot_is_unreachable(monkeypatch):
    monkeypatch.setattr(ai_client, "AI_PROVIDER", "depot")

    def fake_post(url, json, timeout):
        raise httpx.ConnectError("connection refused", request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    reply = ai_client.chat([{"role": "user", "content": "hi"}])
    assert "Could not reach the Depot" in reply
