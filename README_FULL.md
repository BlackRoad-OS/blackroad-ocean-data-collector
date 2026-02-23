# BlackRoad Ocean Data Collector

Comprehensive ocean data collection and marine monitoring system for real-time oceanographic sensor management and analysis.

## Features

### 🌊 Sensor Types
- **Buoy**: Surface platform
- **Argo Float**: Autonomous profiling float
- **Glider**: Autonomous underwater glider
- **Mooring**: Fixed deployment
- **AUV**: Autonomous underwater vehicle
- **CTD**: Conductivity-Temperature-Depth probe

### 📡 Data Collection
- Real-time temperature, salinity, pH, dissolved oxygen monitoring
- Current velocity measurement
- Depth-adaptive sampling
- Sensor status tracking
- Last reading timestamp logging

### 🎯 Anomaly Detection
- **Temperature Alerts**: > 30°C
- **Ocean Acidification**: pH < 7.8
- **Hypoxia Detection**: Dissolved O₂ < 4 mg/L
- Severity classification (Critical, Warning, Info)
- Historical anomaly tracking

### 📊 Analytics
- Fleet status dashboard
- Heat content calculation (integrated oceanographic measurement)
- 24-hour trend analysis
- ASCII heatmap visualization
- NetCDF-style data export

### 🚨 Alert System
- Real-time anomaly detection
- Severity-based alerting
- Summary reporting
- Historical anomaly review

### 🎨 Visualization
- ASCII grid heatmaps by latitude/longitude
- Parameter-specific visualization (temperature, salinity)
- Fleet location plotting

## Installation

```bash
git clone https://github.com/BlackRoad-OS/blackroad-ocean-data-collector.git
cd blackroad-ocean-data-collector
pip install -e .
```

## Usage

### Check Fleet Status
```bash
python src/ocean_collector.py fleet
```

Output:
```json
[
  {
    "id": "S_PACIFIC_01",
    "name": "Pacific Buoy",
    "type": "buoy",
    "lat": 35.5,
    "lon": -120.3,
    "depth_m": 4000,
    "status": "active",
    "last_reading": {
      "temperature_c": 18.2,
      "salinity_psu": 34.5,
      "ph": 8.1,
      "dissolved_o2_mgl": 6.2
    }
  }
]
```

### View Anomalies
```bash
python src/ocean_collector.py anomalies
```

### Display Heatmap
```bash
python src/ocean_collector.py heatmap temperature
python src/ocean_collector.py heatmap salinity
```

### Deploy New Sensor
```bash
python src/ocean_collector.py deploy "Arctic Glider 2" glider 78.5 15.2 3000
```

## Database

SQLite database stored at `~/.blackroad/ocean.db`

### Schema
- **sensors**: Deployed sensor metadata
- **readings**: Time-series oceanographic data
- **anomalies**: Detected anomaly events

### Pre-populated Demo Sensors
1. **Pacific Buoy** (35.5°N, 120.3°W, 4000m)
2. **Atlantic Mooring** (45.2°N, 30.1°W, 5000m)
3. **Arctic Glider** (78.5°N, 15.2°E, 3000m)

## Python API

### Basic Usage
```python
from src.ocean_collector import OceanDataCollector

collector = OceanDataCollector()

# Get fleet status
fleet = collector.fleet_status()
for sensor in fleet:
    print(f"{sensor['name']}: {sensor['last_reading']['temperature_c']}°C")

# Ingest new reading
reading = collector.ingest_reading(
    sensor_id="S_PACIFIC_01",
    temp=18.5,
    salinity=34.6,
    ph=8.09,
    o2=6.1,
    current=0.25
)

# Check for anomalies
anomalies = collector.detect_anomalies()
print(collector.alert_summary())

# Calculate ocean heat content
heat = collector.calculate_heat_content(["S_PACIFIC_01", "S_ATLANTIC_01"])
print(f"Heat Content: {heat['total_heat_content_kj_m2']} kJ/m²")

# Export data
collector.export_netcdf_stub("/tmp/ocean_data.json")

# View heatmap
print(collector.heatmap_ascii("temperature"))
```

## CLI Commands

```bash
# Check all sensors
python src/ocean_collector.py fleet

# View anomalies
python src/ocean_collector.py anomalies

# Display heatmap
python src/ocean_collector.py heatmap [parameter]

# Deploy new sensor
python src/ocean_collector.py deploy <name> <type> <lat> <lon> <depth>
```

## Oceanographic Parameters

### Temperature (°C)
- Normal range: -2 to 30°C
- Alert threshold: > 30°C
- Affects ocean stratification and heat transport

### Salinity (PSU)
- Normal range: 32-36 PSU
- Indicates freshwater input
- Affects water density and currents

### pH
- Ocean baseline: ~8.2
- Alert threshold: < 7.8 (acidification)
- Indicator of CO₂ absorption

### Dissolved Oxygen (mg/L)
- Normal range: 4-10 mg/L
- Alert threshold: < 4 mg/L (hypoxia)
- Critical for marine life

## Data Export

### NetCDF-style JSON
```json
{
  "dimensions": {
    "time": "unlimited",
    "station": 3
  },
  "variables": {
    "temperature": {"units": "degC", "data": [18.2, 12.5, 8.3]},
    "salinity": {"units": "PSU", "data": [34.5, 34.2, 33.8]}
  },
  "metadata": {
    "title": "BlackRoad Ocean Data Collection",
    "created": "2024-01-15T10:30:00"
  }
}
```

## Oceanographic Applications

- Climate change monitoring (heat content, temperature trends)
- Marine ecosystem health (dissolved oxygen, acidification)
- Harmful algal bloom detection
- Marine pollution tracking
- Fisheries management
- Nautical forecasting

## Science References

- Ocean acidification: < pH 7.8
- Hypoxia threshold: < 4 mg/L O₂
- Thermal stratification: Temperature gradients
- Water mass identification: T-S diagrams

## Limitations

This is an educational simulation:
- Simplified physics models
- No water mass dynamics
- No advection/dispersion
- Single-point measurements
- Ideal sensor response

Real-world oceanography involves complex 3D circulation, wave dynamics, and coupled biogeochemical processes.

## License

MIT
