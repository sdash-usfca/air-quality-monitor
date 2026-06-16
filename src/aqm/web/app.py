"""Flask web app: a live dashboard plus a small JSON API.

Flask (pure Python) is used instead of FastAPI because the Pi Zero W is ARMv6 and
has no prebuilt wheels for pydantic-core/uvloop — see docs/ARCHITECTURE.md.
"""
from __future__ import annotations

import time
from typing import Optional

from flask import Flask, jsonify, render_template, request

from ..config import Config, load_config
from ..models import DISPLAY_ORDER, METRICS
from ..storage.db import Database


def create_app(config: Optional[Config] = None) -> Flask:
    config = config or load_config()
    app = Flask(__name__)
    db = Database(config.db_path)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/latest")
    def api_latest():
        latest = db.latest()
        now = int(time.time())
        metrics = []
        for key in DISPLAY_ORDER:
            if key not in latest:
                continue
            value, ts = latest[key]
            spec = METRICS[key]
            metrics.append({
                "key": key,
                "label": spec.label,
                "unit": spec.unit,
                "value": value,
                "display": spec.format(value),
                "status": spec.status(value).value,
                "age_seconds": now - ts,
            })
        return jsonify({"metrics": metrics, "server_time": now})

    @app.route("/api/history")
    def api_history():
        metric = request.args.get("metric", "co2")
        hours = float(request.args.get("hours", 24))
        since = int(time.time() - hours * 3600)
        return jsonify({"metric": metric, "points": db.history(metric, since)})

    @app.route("/api/metrics")
    def api_metrics():
        """Metadata for every metric, so the frontend can build charts + thresholds."""
        out = []
        for key in DISPLAY_ORDER:
            spec = METRICS[key]
            out.append({
                "key": key, "label": spec.label, "unit": spec.unit,
                "good_max": spec.good_max, "moderate_max": spec.moderate_max,
                "precision": spec.precision,
            })
        return jsonify({"metrics": out})

    @app.route("/api/history_all")
    def api_history_all():
        """Downsampled history for all metrics in one request (~`target` points each)."""
        hours = float(request.args.get("hours", 24))
        target = 300
        since = int(time.time() - hours * 3600)
        bucket = max(int(config.interval_seconds), int(hours * 3600 / target) or 1)
        series = {key: db.history_bucketed(key, since, bucket) for key in DISPLAY_ORDER}
        return jsonify({"hours": hours, "bucket_seconds": bucket, "series": series})

    @app.route("/healthz")
    def healthz():
        return jsonify({"ok": True})

    return app


def main() -> None:
    config = load_config()
    app = create_app(config)
    app.run(host=config.web.host, port=config.web.port, threaded=True)
