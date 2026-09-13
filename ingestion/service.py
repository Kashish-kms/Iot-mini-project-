"""MQTT subscriber → SQLite writer + periodic preprocessing.

This is the "cloud ingestion" service for the AIoT stack. It:
  * Connects to the Mosquitto broker over TLS with the `ingest_user`
    credentials; the broker ACL guarantees this identity may only
    SUBSCRIBE to `home/room1/telemetry`, never PUBLISH.
  * Validates the ESP32-drop-in JSON schema on every message.
  * Writes every validated message to SQLite ``telemetry`` table.
  * Every ``PREPROCESS_INTERVAL_SEC`` seconds kicks off the
    ``preprocessing.run_pipeline`` which rebuilds the ``features`` table
    for ML training and live inference.
  * Shuts down cleanly on SIGINT / SIGTERM (MQTT disconnect + DB close).
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

import dotenv
import paho.mqtt.client as mqtt

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ingestion import database as db
    from ingestion import preprocessing
else:
    from . import database as db
    from . import preprocessing


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [ingestion] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("ingestion")


# ---------------------------------------------------------------------------
# Shutdown.
# ---------------------------------------------------------------------------
class _Shutdown:
    flag = False
    cond = threading.Condition()

    @classmethod
    def trigger(cls, *_):
        with cls.cond:
            if not cls.flag:
                cls.flag = True
                log.info("Shutdown signal received — draining in-flight messages.")
                cls.cond.notify_all()


signal.signal(signal.SIGINT, _Shutdown.trigger)
signal.signal(signal.SIGTERM, _Shutdown.trigger)


# ---------------------------------------------------------------------------
# MQTT helpers.
# ---------------------------------------------------------------------------
def _locate_ca_cert(env_ca: Optional[str]) -> Optional[str]:
    candidates = []
    if env_ca:
        candidates.append(env_ca)
    root = Path(__file__).resolve().parent.parent
    candidates.append(root / "broker" / "certs" / "ca.crt")
    candidates.append(Path("/broker/certs/ca.crt"))
    candidates.append(Path("/etc/ssl/certs/broker-ca.crt"))
    for c in candidates:
        p = Path(c)
        if p.exists() and p.is_file():
            return str(p.resolve())
    return None


_EXPECTED_KEYS: tuple = ("timestamp", "temperature", "humidity", "co2", "motion", "room_id")


def _validate_payload(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize a single MQTT payload dict.

    Returns a normalized dict suitable for ``insert_telemetry``.
    Raises ``ValueError`` on schema mismatch so the caller can skip.
    """
    if not isinstance(obj, dict):
        raise ValueError("payload must be a JSON object")
    missing = [k for k in _EXPECTED_KEYS if k not in obj]
    if missing:
        raise ValueError(f"missing keys: {missing}")
    try:
        ts = int(obj["timestamp"])
        temperature = float(obj["temperature"])
        humidity = float(obj["humidity"])
        co2 = float(obj["co2"])
        motion = int(obj["motion"])
        room_id = str(obj["room_id"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"type coercion failed: {exc}") from None
    if motion not in (0, 1):
        raise ValueError(f"motion must be 0 or 1, got {motion}")
    return {
        "ts": ts,
        "temperature": temperature,
        "humidity": humidity,
        "co2": co2,
        "motion": motion,
        "room_id": room_id,
    }


# ---------------------------------------------------------------------------
# Periodic preprocessing worker (separate thread so MQTT loop never blocks).
# ---------------------------------------------------------------------------
def _preprocess_worker(
    db_path: str,
    interval_sec: int,
    first_run_delay_sec: int = 30,
) -> None:
    time.sleep(first_run_delay_sec)
    while not _Shutdown.flag:
        try:
            log.info("Starting periodic preprocessing run")
            feats = preprocessing.run_pipeline(db_path)
            log.info(f"Preprocessing complete — {len(feats)} feature rows")
        except Exception as exc:  # pragma: no cover
            log.exception(f"Preprocessing failed: {exc}")
        # Sleep in small ticks so shutdown is responsive.
        with _Shutdown.cond:
            _Shutdown.cond.wait(timeout=interval_sec)


# ---------------------------------------------------------------------------
# MQTT wiring.
# ---------------------------------------------------------------------------
def build_client(db_conn, topic: str) -> mqtt.Client:
    host = os.environ.get("MQTT_HOST", "broker")
    port = int(os.environ.get("MQTT_PORT", "8883"))
    user = os.environ.get("MQTT_INGEST_USERNAME", os.environ.get("MQTT_USERNAME", "ingest_user"))
    pw = os.environ.get("MQTT_INGEST_PASSWORD", os.environ.get("MQTT_PASSWORD", "ingest_pass"))
    ca = _locate_ca_cert(os.environ.get("MQTT_CA_CERT"))

    client = mqtt.Client(
        client_id=f"ingest-{os.environ.get('ROOM_ID','room1')}-{os.getpid()}",
        clean_session=True,
    )
    client.username_pw_set(user, pw)
    if ca is None:
        log.warning("No broker CA found. Connecting WITHOUT TLS verification.")
    else:
        client.tls_set(ca_certs=ca)
        log.info(f"TLS enabled: {ca}")

    received = {"count": 0}

    def on_connect(c, u, f, rc):
        if rc == 0:
            log.info(f"Connected to broker {host}:{port} as '{user}', subscribing to {topic}")
            c.subscribe(topic, qos=1)
        else:
            log.error(f"Connect FAILED rc={rc}: {mqtt.error_string(rc)}")

    def on_disconnect(c, u, rc):
        if rc != 0:
            log.warning(f"Unexpected disconnect rc={rc}")

    def on_message(c, u, msg):
        try:
            obj = json.loads(msg.payload.decode("utf-8"))
            row = _validate_payload(obj)
            rid = db.insert_telemetry(db_conn, row)
            received["count"] += 1
            log.info(
                "Inserted telemetry id=%d ts=%d T=%.2f°C H=%.2f%% CO2=%.0fppm motion=%d room=%s (total=%d)",
                rid,
                row["ts"],
                row["temperature"],
                row["humidity"],
                row["co2"],
                row["motion"],
                row["room_id"],
                received["count"],
            )
        except (json.JSONDecodeError, ValueError) as exc:
            log.warning(f"Skipping invalid message on {msg.topic}: {exc}")
        except Exception as exc:  # pragma: no cover
            log.exception(f"DB insert failed: {exc}")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    return client


def connect_with_backoff(client) -> None:
    host = os.environ.get("MQTT_HOST", "broker")
    port = int(os.environ.get("MQTT_PORT", "8883"))
    backoff = 1.0
    while not _Shutdown.flag:
        try:
            client.connect(host, port, keepalive=60)
            return
        except OSError as exc:
            log.warning(f"Connect failed ({exc}), retrying in {backoff:.1f}s")
            with _Shutdown.cond:
                _Shutdown.cond.wait(timeout=backoff)
            backoff = min(60.0, backoff * 1.7)


def run_service() -> None:
    dotenv.load_dotenv()
    room_id = os.environ.get("ROOM_ID", "room1")
    topic = f"home/{room_id}/telemetry"
    db_path = os.environ.get("DB_PATH", "./data/iot.db")
    preprocess_interval = int(os.environ.get("PREPROCESS_INTERVAL_SEC", "300"))

    log.info(f"Ingestion service booting: topic={topic}, db={db_path}")
    conn = db.init_db(db_path)

    # Preprocessing thread.
    worker = threading.Thread(
        target=_preprocess_worker,
        args=(db_path, preprocess_interval),
        daemon=True,
        name="preprocess-worker",
    )
    worker.start()

    client = build_client(conn, topic)
    connect_with_backoff(client)
    client.loop_start()
    try:
        while not _Shutdown.flag:
            with _Shutdown.cond:
                _Shutdown.cond.wait(timeout=2.0)
    finally:
        log.info("Stopping MQTT loop + DB connections")
        client.loop_stop()
        try:
            client.disconnect()
        except Exception:
            pass
        db.close_all()
        log.info("Ingestion shut down cleanly.")


if __name__ == "__main__":
    run_service()
