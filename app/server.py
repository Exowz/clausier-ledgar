"""Run the offline Clausier single-page demo and its JSON API."""

import argparse
from collections.abc import Callable

from flask import Flask, jsonify, render_template, request

from app.services import Services


class InputError(ValueError):
    """A request that fails public API validation."""


def create_app(services: Services | None = None) -> Flask:
    """Create the demo app, optionally with a test service implementation."""
    app = Flask(__name__)
    backend = services if services is not None else Services()

    def body_text(body: dict, field: str) -> str:
        value = body.get(field)
        if not isinstance(value, str) or not value.strip():
            raise InputError(f"{field} must not be empty")
        if len(value) > 20_000:
            raise InputError(f"{field} must be at most 20,000 characters")
        return value.strip()

    def model_id(body: dict) -> str:
        model = body.get("model", "tfidf")
        if model not in {row["id"] for row in backend.models()}:
            raise InputError("Unknown model")
        return model

    def post_result(action: Callable[[dict], dict]):
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise InputError("Send a JSON object")
        return jsonify(action(body))

    @app.errorhandler(InputError)
    def input_error(error: InputError):
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(Exception)
    def unexpected_error(error: Exception):
        app.logger.exception("Request failed: %s", error)
        return jsonify({"error": "The request could not be completed."}), 500

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/models")
    def models():
        return jsonify(backend.models())

    @app.post("/api/classify")
    def classify():
        return post_result(lambda body: backend.classify(
            body_text(body, "text"), model_id(body), body.get("explain", True),
        ))

    @app.post("/api/search")
    def search():
        def action(body: dict) -> dict:
            query = body_text(body, "query")
            method = body.get("method", "dense")
            if method not in {"dense", "tfidf", "overlap"}:
                raise InputError("Unknown search method")
            k = body.get("k", 5)
            if not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= 20:
                raise InputError("k must be between 1 and 20")
            return backend.search(query, method, k)

        return post_result(action)

    @app.post("/api/review")
    def review():
        return post_result(lambda body: backend.review(body_text(body, "text"), model_id(body)))

    @app.post("/api/stress")
    def stress():
        return post_result(lambda body: backend.stress(body_text(body, "text"), model_id(body)))

    @app.get("/api/evidence")
    def evidence():
        return jsonify(backend.evidence())

    @app.get("/api/sample-contract")
    def sample_contract():
        return jsonify({"text": backend.sample_contract()})

    return app


def main() -> None:
    """Start the local demo server from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--preload", action="store_true")
    args = parser.parse_args()
    services = Services()
    if args.preload:
        services.preload()
    app = create_app(services)
    print(f"Ready on http://{args.host}:{args.port}", flush=True)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
