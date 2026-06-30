#!/usr/bin/env python3
"""Speak an air-quality alert to a Google Nest / Chromecast when the air goes poor.

Polls the local dashboard API and, when the overall air quality crosses into
"poor", casts a short spoken tip to the speaker (e.g. "Carbon dioxide is high —
open a window"). It re-arms only after the air recovers, and won't repeat more
often than REALERT_SECONDS, so it never nags.

The speech is generated on-device with gTTS, saved into the Flask static folder,
and the speaker is told to fetch it from the Pi over the LAN.

Config via env vars (all optional):
  AQM_SPEAKER       cast device friendly name   (default "Kitchen speaker")
  AQM_API           dashboard API url           (default http://localhost:8000/api/latest)
  AQM_ALERT_LEVEL   "poor" or "moderate"        (default "poor")

Run a one-shot demo (speaks a sample alert and exits):  nest_alert.py --test
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
import urllib.request

import pychromecast
from gtts import gTTS

SPEAKER = os.environ.get("AQM_SPEAKER", "Kitchen speaker")
API = os.environ.get("AQM_API", "http://localhost:8000/api/latest")
ALERT_LEVEL = os.environ.get("AQM_ALERT_LEVEL", "poor")

_HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(_HERE, "..", "src", "aqm", "web", "static")
AUDIO_FILE = "alert.mp3"

POLL_SECONDS = 30
REALERT_SECONDS = 1800   # if it stays bad, re-remind at most every 30 min
RANK = {"good": 0, "moderate": 1, "poor": 2}


def lan_ip() -> str:
    """The Pi's own LAN IP, so the speaker can fetch audio from us."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def worst_status(metrics):
    worst = "good"
    for m in metrics:
        s = m.get("status")
        if s in RANK and RANK[s] > RANK[worst]:
            worst = s
    drivers = [m for m in metrics if m.get("status") == worst and worst != "good"]
    return worst, drivers


def message_for(drivers) -> str:
    have_co2 = any(m["key"] == "co2" for m in drivers)
    have_pm = any(m["key"].startswith("pm") for m in drivers)
    co2v = next((m["display"] for m in drivers if m["key"] == "co2"), None)
    tips = []
    if have_co2:
        tips.append(f"Carbon dioxide is high at {co2v} parts per million. "
                    "Open a window or improve ventilation.")
    if have_pm:
        tips.append("Particulate levels are elevated. "
                    "Check for smoke or cooking, and consider an air purifier.")
    if not tips:
        tips.append("Air quality has dropped.")
    return "Heads up. " + " ".join(tips)


def speak(text: str) -> bool:
    """Generate speech and cast it to the speaker. Returns True if it played."""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    gTTS(text, lang="en").save(os.path.join(AUDIO_DIR, AUDIO_FILE))
    url = f"http://{lan_ip()}:8000/static/{AUDIO_FILE}?t={int(time.time())}"

    casts, browser = pychromecast.get_chromecasts(timeout=12)
    try:
        cast = next((c for c in casts if c.cast_info.friendly_name == SPEAKER), None)
        if cast is None:
            print(f"nest_alert: speaker {SPEAKER!r} not found", file=sys.stderr)
            return False
        cast.wait()
        cast.set_volume(0.55)
        mc = cast.media_controller
        mc.play_media(url, "audio/mpeg")
        mc.block_until_active(timeout=15)
        for _ in range(12):
            time.sleep(1)
            if mc.status.player_state == "IDLE":
                break
        return True
    finally:
        try:
            pychromecast.discovery.stop_discovery(browser)
        except Exception:
            pass


def main() -> None:
    if "--test" in sys.argv:
        ok = speak("Heads up. This is a test of your air quality alerts. "
                   "Carbon dioxide is high at 1300 parts per million. "
                   "Open a window or improve ventilation.")
        print("test cast:", "played" if ok else "FAILED")
        return

    print(f"nest_alert: watching {API}; alerting {SPEAKER!r} at level >= {ALERT_LEVEL}")
    armed = True   # may fire when armed and air is bad
    last_alert = 0.0
    while True:
        try:
            with urllib.request.urlopen(API, timeout=8) as r:
                metrics = json.load(r)["metrics"]
            worst, drivers = worst_status(metrics)
            bad = RANK[worst] >= RANK[ALERT_LEVEL]
            now = time.time()
            if bad and (armed or now - last_alert > REALERT_SECONDS):
                if speak(message_for(drivers)):
                    armed = False
                    last_alert = now
                    print(f"nest_alert: spoke ({worst})")
            elif not bad:
                armed = True   # recovered — re-arm for the next episode
        except Exception as e:  # noqa: BLE001 — keep the daemon alive
            print("nest_alert error:", e, file=sys.stderr)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
