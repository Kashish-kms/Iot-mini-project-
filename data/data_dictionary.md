# VeilSense Sensor Data Dictionary

| Variable Name | Type | Physical Unit | Description | Privacy Consideration |
| :--- | :--- | :--- | :--- | :--- |
| `timestamp` | Datetime (ISO 8601) | UTC / Local Time | Recorded timestamp of the 30-second edge window | No individual user identity linked |
| `temperature` | Float | Degrees Celsius (°C) | Ambient thermal measurement from DHT22 calibrated sensor | Non-identifying environmental context |
| `humidity` | Float | Relative Humidity (% RH) | Relative moisture content from DHT22 capacitive element | Non-identifying environmental context |
| `air_quality_ppm` | Float | PPM (Parts Per Million) | MQ-135 semiconductor sensor output, sensitive to CO2, CO, NH3, benzene, smoke | Non-identifying ambient air composition |
| `motion_detected` | Integer (0 or 1) | Binary Flag | PIR infrared thermal movement detected during the 30s aggregate window | **Zero image/audio**, only ambient infrared variance |
| `motion_count` | Integer | Count | Number of discrete motion trigger pulses during the 30s window | Quantifies room activity intensity |
| `fan_active` | Integer (0 or 1) | Binary Flag | Actuation state of ventilation air exchange fan | Smart building state |
| `is_outlier` | Integer (0 or 1) | Binary Flag | Flagged by IQR / range validation filter as physical or electrical anomaly | Quality assurance |
| `risk_level` | Integer (0, 1, 2) | Categorical | 0 = Safe, 1 = Moderate Risk, 2 = High Risk (Air stagnation / discomfort / hazards) | ML target label |
