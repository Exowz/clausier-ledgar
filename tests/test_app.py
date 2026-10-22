"""Offline tests for the demo app's API and service adapters."""

import numpy as np
import pytest

from app.server import create_app
from app.services import Services


class FakeServices:
    """Return recognizable responses without loading project artifacts."""

    def models(self):
        return [{"id": "tfidf", "name": "TF-IDF", "recommended": True}]

    def classify(self, text, model, explain=True):
        return {"type": "Governing Laws", "text": text, "explain": explain}

    def search(self, query, method="dense", k=5):
        return {"query": query, "method": method, "k": k}

    def review(self, text, model):
        return {"clauses": [{"text": text}], "checklist": []}

    def stress(self, text, model):
        return {"original": text, "edits": []}

    def evidence(self):
        return {"results": []}

    def sample_contract(self):
        return "A sample contract."


@pytest.fixture
def client():
    """Create a Flask client with no saved models or downloads."""
    return create_app(FakeServices()).test_client()


def test_page_and_read_routes(client):
    assert client.get("/").status_code == 200
    assert b"Clausier" in client.get("/").data
    assert client.get("/api/models").json[0]["id"] == "tfidf"
    assert client.get("/api/evidence").json == {"results": []}
    assert client.get("/api/sample-contract").json == {"text": "A sample contract."}


@pytest.mark.parametrize("route,body,expected", [
    ("classify", {"text": "A clause", "model": "tfidf", "explain": False},
     {"type": "Governing Laws", "text": "A clause", "explain": False}),
    ("search", {"query": "a query", "method": "tfidf", "k": 3}, {"query": "a query", "method": "tfidf", "k": 3}),
    ("review", {"text": "A clause", "model": "tfidf"}, {"clauses": [{"text": "A clause"}], "checklist": []}),
    ("stress", {"text": "A clause", "model": "tfidf"}, {"original": "A clause", "edits": []}),
])
def test_post_routes(client, route, body, expected):
    response = client.post(f"/api/{route}", json=body)
    assert response.status_code == 200
    assert response.json == expected


@pytest.mark.parametrize("route,key", [
    ("classify", "text"), ("search", "query"), ("review", "text"), ("stress", "text"),
])
def test_empty_input(client, route, key):
    response = client.post(f"/api/{route}", json={key: "  ", "model": "tfidf"})
    assert response.status_code == 400
    assert "error" in response.json


@pytest.mark.parametrize("route", ["classify", "review", "stress"])
def test_unknown_model(client, route):
    response = client.post(f"/api/{route}", json={"text": "A clause", "model": "unknown"})
    assert response.status_code == 400


def test_invalid_search_method_and_length(client):
    assert client.post("/api/search", json={"query": "hello", "method": "bad"}).status_code == 400
    assert client.post("/api/classify", json={"text": "a" * 20001, "model": "tfidf"}).status_code == 400


def test_evidence_missing_files(tmp_path):
    result = Services(tmp_path).evidence()
    assert result["results"] == "not available"
    assert result["paired_test"] == "not available"
    assert result["calibration"]["tfidf"] == "not available"
    assert result["retrieval"] == "not available"
    assert result["cost"] == "not available"


def test_stress_applies_only_relevant_edits(tmp_path):
    class Classifier:
        def predict_proba(self, texts):
            return np.tile([0.1, 0.9], (len(texts), 1))

    services = Services(tmp_path)
    services._classifiers["tfidf"] = Classifier()
    services._label_names = ["Other", "Governing Laws"]
    result = services.stress("Licensor and Licensee choose New York law.", "tfidf")
    assert [row["applies"] for row in result["edits"]] == [True, True, False]
    assert result["edits"][0]["changed_words"]
