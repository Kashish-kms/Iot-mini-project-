"""Tunable configuration for the synthetic indoor IoT sensor simulator.

Default ranges are based on typical published indoor residential/office
environments:
    - Temperature: ASHRAE Thermal Comfort Guideline suggests 20-26 °C for
      sedentary activity in summer/winter. We use a baseline of 21 °C with a
      daily sinusoid of ±2 °C, producing a realistic ~19-23 °C diurnal swing
      before drift and noise.
    - Relative Humidity: EPA / ASHRAE recommend 30-60 % for indoor air quality;
      our baseline of 45 % plus noise keeps values comfortably inside this
      band most of the time.
    - CO2: Outdoor ambient is currently ~420 ppm. Well-ventilated unoccupied
      indoor spaces hover close to that; a single occupant adds roughly
      400-800 ppm above baseline depending on room size and ventilation
      (ref: ASHRAE 62.1 / Lawrence Berkeley National Laboratory studies on
      human CO2 emission rates, ~0.005 L/s per adult at rest).
    - Occupancy pattern: a Poisson arrival rate of 2 events/hour with mean
      duration 30 minutes roughly models occasional room use (home office,
      bedroom, meeting room). Tune these to simulate denser or sparser use.

The privacy-preserving mechanism lives in the interaction between
SAMPLING_INTERVAL_SEC (high-frequency internal raw samples) and
AGGREGATION_WINDOW_SEC (the only cadence that ever leaves the simulator).
A real ESP32-class edge device would do the same aggregation on-chip before
MQTT publish, preventing motion/temperature fingerprinting from per-second
samples ever traversing the network.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """All tunable parameters for ``SensorGenerator`` + ``publisher.py``.

    Values can be overridden via environment variables (useful for
    docker-compose or per-run experiments) by matching the field name.
    """

    # ------------------------------------------------------------------
    # Thermal / humidity baselines
    # ------------------------------------------------------------------
    BASELINE_TEMP_C: float = 21.0
    """Mean indoor temperature (°C). ASHRAE comfort center for sedentary
    occupancy in mixed-mode buildings."""

    TEMP_DAILY_AMPLITUDE_C: float = 2.0
    """Peak-to-mean amplitude (°C) of the daily sinusoid. 2 °C gives a
    ~4 °C peak-to-trough swing, consistent with poorly-zoned residential
    HVAC or passive solar gain in an office."""

    TEMP_NOISE_STD: float = 0.3
    """Standard deviation (°C) of additive Gaussian sensor noise. Typical
    for a low-cost DHT22 / BME280 class temperature sensor after 10x
    oversampling."""

    TEMP_DRIFT_STD_PER_SEC: float = 0.0005
    """Per-second standard deviation of the slow cumulative drift random
    walk. Clipped to ±2 °C overall. Simulates long-term sensor drift or
    slow HVAC setback changes."""

    BASELINE_HUMIDITY_PCT: float = 45.0
    """Mean indoor relative humidity (%). Center of the EPA/ASHRAE 30-60 %
    healthy IAQ band."""

    HUMIDITY_NOISE_STD: float = 1.5
    """Additive Gaussian noise σ for humidity (%). Again aligned with
    typical DHT22 long-term repeatability specs."""

    HUMIDITY_DRIFT_STD_PER_SEC: float = 0.002
    """Per-second σ for slow humidity random walk. Clipped to ±10 %."""

    HUMIDITY_TEMP_COUPLING: float = -2.0
    """Inverse coupling: as temp goes up 1 °C, RH drops by ~this many
    percentage points (rough Clausius-Clapeyron scaling for constant
    absolute humidity inside a sealed room)."""

    # ------------------------------------------------------------------
    # CO2 + occupancy state machine
    # ------------------------------------------------------------------
    BASELINE_CO2_PPM: float = 420.0
    """Unoccupied well-ventilated steady-state CO2. Matches ~2025 global
    Mauna Loa atmospheric CO2."""

    CO2_NOISE_STD: float = 20.0
    """Additive Gaussian sensor noise σ (ppm). Typical for an MQ-135 /
    SCD4x class low-cost NDIR sensor at low concentrations."""

    OCCUPANCY_CO2_SPIKE_PPM: float = 650.0
    """Asymptotic CO2 elevation above baseline caused by one average
    occupant breathing in a modestly ventilated ~30 m³ room. Roughly
    emission / air-changes-per-hour steady-state."""

    OCCUPANCY_CO2_TAU_SEC: float = 10.0 * 60.0
    """Time constant (seconds) of the first-order CO2 rise/decay during
    occupancy transitions. 10 minutes gives realistic S-shaped curves
    rather than instant steps."""

    OCCUPANCY_EVENT_RATE_PER_HOUR: float = 2.0
    """Poisson arrival rate λ for new occupancy events per wall-clock
    hour. 2/h ≈ a meeting room booked every ~30 minutes on average."""

    OCCUPANCY_DURATION_MIN_MEAN: float = 30.0
    """Exponential mean event duration (minutes). Occupancy events are
    memoryless given this mean — realistic for drop-in office use."""

    MOTION_PROB_WHILE_OCCUPIED: float = 0.90
    """Per-sample probability PIR-equivalent fires when room is
    occupied. High but not 1.0 (occupants do sit still for a while)."""

    MOTION_PROB_WHILE_VACANT: float = 0.02
    """Per-sample false-positive PIR probability while room is vacant:
    pet, dust, air-current, or direct-sun artifact."""

    # ------------------------------------------------------------------
    # Timing + privacy aggregation
    # ------------------------------------------------------------------
    SAMPLING_INTERVAL_SEC: float = 5.0
    """Internal raw sampling cadence (seconds). NEVER published — this is
    the "edge-only" high-frequency data that is privacy-sensitive because
    per-second motion patterns can fingerprint room activity."""

    AGGREGATION_WINDOW_SEC: float = 60.0
    """Privacy-preserving on-simulator aggregation window (seconds). Only
    one summary tuple per window is ever handed to publisher.py — the
    raw SAMPLING_INTERVAL_SEC samples are discarded immediately after
    averaging. This is the project's data-minimization primitive. A
    future hardware drop-in must perform the identical aggregation on
    the ESP32 before MQTT publish."""

    # ------------------------------------------------------------------
    # Reproducibility: these enable seed-split ML evaluation later
    # ------------------------------------------------------------------
    RANDOM_SEED: int = 42
    """Master random seed. Two runs with identical seeds + starting
    epoch produce byte-identical aggregated outputs."""

    SCENARIO_SEED: int = 1
    """Secondary seed that modulates occupancy pattern characteristics
    (e.g. shifts typical meeting times, skews durations). Used by
    ml/evaluate.py to split train/test *by scenario group*, never by
    random row shuffle, to test generalization."""

    SIMULATED_START_HOUR: float = 6.0
    """Wall-clock hour at which the virtual sensor boots. Lets us align
    the sinusoid and scenario to a realistic morning start."""

    # ------------------------------------------------------------------
    # Identity + transport
    # ------------------------------------------------------------------
    ROOM_ID: str = "room1"
    """Logical room id used in the MQTT topic and the ``room_id`` JSON
    field. Must match the ACL topic path on the broker."""

    MQTT_TOPIC_TEMPLATE: str = "home/{room_id}/telemetry"
    """MQTT topic format. Kept deliberately identical to what a real
    ESP32 + DHT22 + MQ-135 + PIR node would publish so broker /
    ingestion / ML require zero changes on a future hardware drop-in."""

    MQTT_QOS: int = 1
    """MQTT QoS. QoS 1 is appropriate for periodic telemetry where
    occasional duplicates are harmless but drops are undesirable."""

    @staticmethod
    def from_env(overrides: Optional[dict] = None) -> "Config":
        """Build a Config, overriding any field from a matching uppercase
        environment variable. Also accepts an explicit ``overrides`` dict
        for programmatic tweaks."""
        import os as _os

        fields = {f.name: f.default for f in Config.__dataclass_fields__.values()}
        values: dict = {}
        for name, default in fields.items():
            raw = _os.environ.get(name)
            if raw is not None:
                values[name] = type(default)(raw)
            else:
                values[name] = default
        if overrides:
            values.update(overrides)
        return Config(**values)

    @property
    def mqtt_topic(self) -> str:
        return self.MQTT_TOPIC_TEMPLATE.format(room_id=self.ROOM_ID)

    @property
    def samples_per_window(self) -> int:
        """Number of internal raw samples aggregated per published tuple."""
        return max(1, int(round(self.AGGREGATION_WINDOW_SEC / self.SAMPLING_INTERVAL_SEC)))


if __name__ == "__main__":
    cfg = Config.from_env()
    print("Simulator Config:")
    for k, v in cfg.__dict__.items():
        print(f"  {k} = {v!r}")
    print(f"  mqtt_topic       -> {cfg.mqtt_topic}")
    print(f"  samples_per_window -> {cfg.samples_per_window}")
