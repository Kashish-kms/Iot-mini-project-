"""Synthetic indoor sensor simulator with on-board privacy aggregation.

``SensorGenerator`` is the entire synthetic sensor layer. It produces
per-``SAMPLING_INTERVAL_SEC`` raw samples internally (temperature,
humidity, CO2, motion) and **only** emits one aggregated summary per
``AGGREGATION_WINDOW_SEC``. The internal samples are discarded after
averaging — they are never returned, never logged, and never handed to
the publisher. This on-simulator (analogous to on-edge) aggregation is
the project's data-minimization / privacy primitive.

Signal models
-------------
* temperature : daily sinusoid + slow drift random walk + Gaussian noise.
* humidity    : inverse-coupled to temperature (constant absolute humidity
                approximation) + its own drift + noise.
* occupancy   : Poisson arrival + exponential-duration state machine.
* co2         : baseline + first-order rise/decay toward an occupancy-
                dependent asymptote, plus sensor noise.
* motion      : Bernoulli per raw sample with occupancy-driven bias
                (high p if occupied, very low p if vacant). Aggregated to
                ``max(motion)`` over the window (i.e. "was there ANY
                motion in this minute" — just like a latching PIR).
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from .config import Config


# ---------------------------------------------------------------------------
# Private raw-sample dataclass — intentionally not exported.
# Nothing outside this file ever sees individual raw samples.
# ---------------------------------------------------------------------------
@dataclass
class _RawSample:
    ts_ms: int
    temperature: float
    humidity: float
    co2: float
    motion: int
    occupied: bool


class SensorGenerator:
    """Generate realistic aggregated indoor IoT sensor tuples.

    Parameters
    ----------
    config : Config
        All tunable constants. A copy is used internally; the caller's
        object is not mutated.
    start_epoch_ms : Optional[int]
        Virtual wall-clock epoch at which the sensor "boots". If None,
        the current real epoch is used.
    """

    def __init__(self, config: Config, start_epoch_ms: Optional[int] = None):
        self.cfg = Config(**{**config.__dict__})

        # Deterministic RNG — guarantees reproducibility across runs with
        # identical seed + start_epoch.
        master_seed = int(config.RANDOM_SEED) ^ (int(config.SCENARIO_SEED) << 16)
        self._rng = np.random.default_rng(master_seed)

        # Virtual sensor wall-clock.
        if start_epoch_ms is None:
            start_epoch_ms = int(time.time() * 1000)
        self._epoch_ms: int = start_epoch_ms
        # Align the first window to an even AGGREGATION_WINDOW_SEC boundary.
        start_s = math.floor(start_epoch_ms / 1000.0)
        offset = start_s % int(self.cfg.AGGREGATION_WINDOW_SEC)
        self._epoch_s: float = float(start_s - offset + self.cfg.SIMULATED_START_HOUR * 3600)
        self._start_epoch_s = self._epoch_s

        # Internal drift state.
        self._temp_drift = 0.0
        self._hum_drift = 0.0

        # Occupancy state machine.
        self._occupied: bool = False
        self._next_event_s: float = 0.0
        self._schedule_next_occupancy_event(reset=True)

        # CO2 first-order state.
        self._co2_state: float = self.cfg.BASELINE_CO2_PPM

    # ------------------------------------------------------------------
    # Public API — these are the ONLY ways to get data out of the
    # generator. Callers never see internal _RawSample objects.
    # ------------------------------------------------------------------
    def next_window(self) -> Dict:
        """Return exactly one aggregated window of readings.

        Internally advances ``samples_per_window`` raw samples, then
        aggregates them. The raw samples are discarded on return.

        Returns
        -------
        dict
            ESP32-drop-in compatible payload schema with no simulator-
            private fields (no drift, no asymptote, no per-sample data):

                {"timestamp":   int   (epoch ms, window end),
                 "temperature": float (°C, mean over window),
                 "humidity":    float (%,  mean over window),
                 "co2":         int   (ppm, rounded mean over window),
                 "motion":      int   (0 or 1, max over window — latching PIR),
                 "room_id":     str}
        """
        buf: List[_RawSample] = []
        for _ in range(self.cfg.samples_per_window):
            buf.append(self._draw_raw_sample())
            self._epoch_s += self.cfg.SAMPLING_INTERVAL_SEC

        agg = self._aggregate_window(buf)
        # Internal raw samples are explicitly dropped — never serialized,
        # never logged, never returned.
        del buf
        return agg

    def generate_batch(self, n_windows: int) -> List[Dict]:
        """Convenience: return ``n_windows`` aggregated dicts in a list."""
        return [self.next_window() for _ in range(n_windows)]

    # ------------------------------------------------------------------
    # Internal signal model helpers.
    # ------------------------------------------------------------------
    def _schedule_next_occupancy_event(self, reset: bool = False) -> None:
        """Occupancy state machine. Poisson arrivals, exponential durations.

        Uses the scenario seed to tweak the mean event rate so that
        different SCENARIO_SEED values produce genuinely different
        occupancy patterns (used later for seed-split ML evaluation)."""
        rate_per_hour = self.cfg.OCCUPANCY_EVENT_RATE_PER_HOUR
        # ±40 % scenario-dependent modulation.
        scenario_shift = (hash(self.cfg.SCENARIO_SEED) % 1000) / 1000.0
        rate_per_hour *= 0.6 + 0.8 * scenario_shift
        mean_inter_sec = 3600.0 / rate_per_hour

        if reset:
            # Boot the sensor ~half an inter-arrival away so runs don't
            # always start with a fresh occupancy event.
            self._next_event_s = self._epoch_s + 0.5 * mean_inter_sec
            self._occupied = False
            return

        if not self._occupied:
            # Transition vacant -> occupied.
            gap = self._rng.exponential(mean_inter_sec)
            self._next_event_s = self._epoch_s + max(5.0, gap)
        else:
            # Transition occupied -> vacant.
            mean_dur_s = self.cfg.OCCUPANCY_DURATION_MIN_MEAN * 60.0 * (
                0.7 + 0.6 * scenario_shift
            )
            dur = self._rng.exponential(mean_dur_s)
            self._next_event_s = self._epoch_s + max(30.0, dur)
        self._occupied = not self._occupied

    def _draw_raw_sample(self) -> _RawSample:
        # Advance the occupancy state machine to current wall-clock.
        while self._epoch_s >= self._next_event_s:
            # Jump clock to event time, toggle, then re-schedule.
            self._epoch_s = self._next_event_s
            self._schedule_next_occupancy_event()

        # ---- Temperature ------------------------------------------------
        day_phase = 2.0 * math.pi * (self._epoch_s / 86400.0)
        # Daily sinusoid peaks at ~15:00 (phase 0 at midnight).
        temp_sin = self.cfg.TEMP_DAILY_AMPLITUDE_C * math.sin(
            day_phase - math.pi / 2.0  # peak at day_phase = π → 12h
        )
        self._temp_drift += self._rng.normal(
            0.0, self.cfg.TEMP_DRIFT_STD_PER_SEC * self.cfg.SAMPLING_INTERVAL_SEC
        )
        self._temp_drift = float(np.clip(self._temp_drift, -2.0, 2.0))
        temp_noise = self._rng.normal(0.0, self.cfg.TEMP_NOISE_STD)
        temperature = (
            self.cfg.BASELINE_TEMP_C + temp_sin + self._temp_drift + temp_noise
        )

        # ---- Humidity (inverse-coupled to temperature, constant abs-h) --
        self._hum_drift += self._rng.normal(
            0.0, self.cfg.HUMIDITY_DRIFT_STD_PER_SEC * self.cfg.SAMPLING_INTERVAL_SEC
        )
        self._hum_drift = float(np.clip(self._hum_drift, -10.0, 10.0))
        hum_noise = self._rng.normal(0.0, self.cfg.HUMIDITY_NOISE_STD)
        temp_delta_from_baseline = temperature - self.cfg.BASELINE_TEMP_C
        humidity = (
            self.cfg.BASELINE_HUMIDITY_PCT
            + self.cfg.HUMIDITY_TEMP_COUPLING * temp_delta_from_baseline
            + self._hum_drift
            + hum_noise
        )
        humidity = float(np.clip(humidity, 1.0, 99.0))

        # ---- CO2 (first-order rise/decay) ------------------------------
        co2_target = self.cfg.BASELINE_CO2_PPM
        if self._occupied:
            co2_target += self.cfg.OCCUPANCY_CO2_SPIKE_PPM
        tau = self.cfg.OCCUPANCY_CO2_TAU_SEC
        alpha = 1.0 - math.exp(-self.cfg.SAMPLING_INTERVAL_SEC / tau)
        self._co2_state += alpha * (co2_target - self._co2_state)
        co2 = self._co2_state + self._rng.normal(0.0, self.cfg.CO2_NOISE_STD)
        co2 = float(np.clip(co2, 350.0, 5000.0))

        # ---- Motion (PIR equivalent) ------------------------------------
        p = (
            self.cfg.MOTION_PROB_WHILE_OCCUPIED
            if self._occupied
            else self.cfg.MOTION_PROB_WHILE_VACANT
        )
        motion = 1 if self._rng.random() < p else 0

        ts_ms = int(round(self._epoch_s * 1000.0))
        return _RawSample(
            ts_ms=ts_ms,
            temperature=round(temperature, 3),
            humidity=round(humidity, 3),
            co2=co2,
            motion=motion,
            occupied=self._occupied,
        )

    @staticmethod
    def _aggregate_window(buf: List[_RawSample]) -> Dict:
        """Privacy-preserving window aggregation.

        Only summary statistics survive here — the per-sample motion
        pattern that could fingerprint room activity is thrown away.
        """
        n = len(buf)
        last = buf[-1]
        temp_mean = sum(s.temperature for s in buf) / n
        hum_mean = sum(s.humidity for s in buf) / n
        co2_mean = sum(s.co2 for s in buf) / n
        # Latching PIR equivalent: did we see ANY motion in the window?
        motion_max = max(s.motion for s in buf)
        return {
            "timestamp": last.ts_ms,
            "temperature": round(temp_mean, 2),
            "humidity": round(hum_mean, 2),
            "co2": int(round(co2_mean)),
            "motion": int(motion_max),
            "room_id": Config().ROOM_ID,  # overridden in __init__ when needed
        }

    def _override_room_id(self, room_id: str) -> None:
        """Allow publisher to inject cfg.ROOM_ID without polluting signal code."""
        # Wrap _aggregate_window to use the configured room id.
        orig = self._aggregate_window

        def patched(buf: List[_RawSample]) -> Dict:
            agg = orig(buf)
            agg["room_id"] = room_id
            return agg

        self._aggregate_window = patched  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Standalone smoke test.
#   > python simulator/generator.py
# Prints 10 aggregated windows plus a small columnar summary.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from .config import Config as _Config

    cfg = _Config.from_env()
    gen = SensorGenerator(cfg)
    gen._override_room_id(cfg.ROOM_ID)

    header = (
        f"{'timestamp(ms)':>15}  {'T(°C)':>6}  {'H(%)':>6}  "
        f"{'CO2(ppm)':>8}  {'motion':>6}  {'room':<6}"
    )
    print(header)
    print("-" * len(header))
    rows = gen.generate_batch(10)
    for r in rows:
        print(
            f"{r['timestamp']:>15}  {r['temperature']:>6.2f}  "
            f"{r['humidity']:>6.2f}  {r['co2']:>8}  {r['motion']:>6}  "
            f"{r['room_id']:<6}"
        )

    # Short sanity summary for CI / quick visual check.
    temps = [r["temperature"] for r in rows]
    hums = [r["humidity"] for r in rows]
    co2s = [r["co2"] for r in rows]
    motions = [r["motion"] for r in rows]
    print()
    print("Sanity ranges over 10 windows:")
    print(f"  temperature: min={min(temps):.2f}°C  max={max(temps):.2f}°C  (expected ~18-28 °C, nominal 19-23)")
    print(f"  humidity   : min={min(hums):.2f}%   max={max(hums):.2f}%   (expected ~30-70 %)")
    print(f"  co2        : min={min(co2s)} ppm   max={max(co2s)} ppm   (expected 400-2000+)")
    print(f"  motion     : any fired={1 if any(motions) else 0} (values must be 0 or 1)")
