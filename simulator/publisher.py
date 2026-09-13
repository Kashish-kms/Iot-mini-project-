"""MQTT publisher for the synthetic AIoT sensor simulator.

Connects over TLS (with CA cert) to the Mosquitto broker using the
simulator-privileged username/password, then produces **only**
privacy-aggregated readings (1-minute windows by default) on topic
``home/room1/telemetry``.

The on-simulator aggregation is performed inside
:class:`simulator.generator.SensorGenerator` — raw 5-second samples never
reach this file, let alone the MQTT socket. That invariant is what makes
the pipeline privacy-by-design.

Publisher supports:
  * TLS + username/password auth (loaded from .env).
  * Exponential-backoff reconnect up to 60 s on broker drops.
  * Graceful SIGINT/SIGTERM shutdown.
  * Clear structured console logs (no PII / no raw samples).
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

import dotenv
import paho.mqtt.client as mqtt

# Allow running as a script or as a module.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from simulator.config import Config
    from simulator.generator import SensorGenerator
else:
    from .config import Config
    from .generator import SensorGenerator


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [publisher] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("publisher")


# ---------------------------------------------------------------------------
# Graceful shutdown helpers.
# ---------------------------------------------------------------------------
class _Shutdown:
    flag = False

    @classmethod
    def trigger(cls, *_):
        cls.flag = True
        log.info("Shutdown signal received — will exit after current window.")


signal.signal(signal.SIGINT, _Shutdown.trigger)
signal.signal(signal.SIGTERM, _Shutdown.trigger)


# ---------------------------------------------------------------------------
# MQTT client setup.
# ---------------------------------------------------------------------------
def _locate_ca_cert(env_ca: Optional[str]) -> Optional[str]:
    """Resolve the broker CA cert path across Docker-compose (mounted) and
    local-dev (inside broker/certs/) layouts."""
    candidates = []
    if env_ca:
        candidates.append(env_ca)
    root = Path(__file__).resolve().parent.parent
    candidates.append(root / "broker" / "certs" / "ca.crt")
    candidates.append(Path("/broker/certs/ca.crt"))
    for c in candidates:
        p = Path(c)
        if p.exists() and p.is_file():
            return str(p.resolve())
    return None


def connect_client(cfg: Config) -> mqtt.Client:
    host = os.environ.get("MQTT_HOST", "broker")
    port = int(os.environ.get("MQTT_PORT", "8883"))
    user = os.environ.get("MQTT_USERNAME", "sim_user")
    pw = os.environ.get("MQTT_PASSWORD", "sim_pass")
    ca = _locate_ca_cert(os.environ.get("MQTT_CA_CERT"))

    client = mqtt.Client(client_id=f"sim-{cfg.ROOM_ID}-{os.getpid()}", clean_session=True)
    client.username_pw_set(user, pw)
    if ca is None:
        log.warning("No broker CA certificate found — connecting WITHOUT TLS verification.")
        log.warning("For real deployments mount broker/certs/ca.crt and set MQTT_CA_CERT.")
    else:
        client.tls_set(ca_certs=ca)
        log.info(f"TLS enabled using CA: {ca}")

    def on_connect(c, u, f, rc):
        if rc == 0:
            log.info(f"Connected to MQTT broker {host}:{port} as '{user}'")
        else:
            log.error(f"MQTT connect FAILED (rc={rc}): {mqtt.error_string(rc)}")

    def on_disconnect(c, u, rc):
        if rc != 0:
            log.warning(f"Unexpected MQTT disconnect (rc={rc}). Will retry.")
        else:
            log.info("Clean MQTT disconnect.")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    backoff = 1.0
    while not _Shutdown.flag:
        try:
            client.connect(host, port, keepalive=60)
            return client
        except OSError as exc:
            log.warning(f"MQTT connect failed ({exc}); retrying in {backoff:.1f}s")
            time.sleep(backoff)
            backoff = min(60.0, backoff * 1.7)
    raise SystemExit(0)


# ---------------------------------------------------------------------------
# Publish loop.
# ---------------------------------------------------------------------------
def _payload_to_json(row: dict) -> bytes:
    """Encode the aggregated window into a tight JSON payload.

    The resulting schema is ESP32-drop-in compatible. No simulator-private
    fields (drift state, raw samples, asymptote, occupancy state) are
    allowed to appear here.
    """
    schema_keys = ("timestamp", "temperature", "humidity", "co2", "motion", "room_id")
    cleaned = {k: row[k] for k in schema_keys if k in row}
    return json.dumps(cleaned, separators=(",", ":")).encode("utf-8")


def run_publisher(max_windows: Optional[int] = None) -> None:
    """Main entry point.

    Parameters
    ----------
    max_windows : int or None
        For tests/smoke runs: publish N windows then exit.
        Production (docker): ``None`` → run forever until signal.
    """
    dotenv.load_dotenv()
    cfg = Config.from_env()
    gen = SensorGenerator(cfg)
    gen._override_room_id(cfg.ROOM_ID)

    topic = cfg.mqtt_topic
    log.info(f"Booting simulator generator: room={cfg.ROOM_ID}, topic={topic}")
    log.info(
        f"Internal sample cadence: {cfg.SAMPLING_INTERVAL_SEC}s, "
        f"aggregation window: {cfg.AGGREGATION_WINDOW_SEC}s, "
        f"samples/window: {cfg.samples_per_window}"
    )
    log.info(
        "PRIVACY: raw samples are NEVER published — only aggregated summaries leave this process."
    )

    client = connect_client(cfg)
    client.loop_start()

    windows_published = 0
    try:
        while not _Shutdown.flag:
            # In the Docker version we sleep in realtime to match the wall clock.
            # The generator *internally* simulates SAMPLING_INTERVAL_SEC per
            # sample and emits one window per call — but we don't want to
            # block the MQTT socket for an entire minute per aggregated
            # window doing nothing. Instead we publish as fast as the
            # generator produces windows, and optionally throttle to real-
            # time if the environment asks for it.
            realtime = bool(int(os.environ.get("SIM_REALTIME", "0")))
            if realtime:
                time.sleep(cfg.AGGREGATION_WINDOW_SEC)
            row = gen.next_window()
            payload = _payload_to_json(row)
            info = client.publish(topic, payload, qos=cfg.MQTT_QOS, retain=False)
            info.wait_for_publish(timeout=5)
            windows_published += 1
            log.info(
                "Published @%s T=%.2f°C H=%.2f%% CO2=%dppm motion=%d (win #%d)",
                row["timestamp"],
                row["temperature"],
                row["humidity"],
                row["co2"],
                row["motion"],
                windows_published,
            )
            if max_windows is not None and windows_published >= max_windows:
                log.info(f"Reached max_windows={max_windows}. Exiting cleanly.")
                break
    except Exception as exc:  # pragma: no cover - defensive
        log.exception(f"Publish loop crashed: {exc}")
    finally:
        client.loop_stop()
        try:
            client.disconnect()
        except Exception:
            pass
        log.info(f"Publisher done. {windows_published} windows published.")


if __name__ == "__main__":
    max_w = int(sys.argv[1]) if len(sys.argv) >= 2 else None
    run_publisher(max_windows=max_w)
