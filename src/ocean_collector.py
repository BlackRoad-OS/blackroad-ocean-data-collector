#!/usr/bin/env python3
"""
Ocean data collection and marine monitoring system.
Real-time oceanographic sensor data management and analysis.
"""

import os
import json
import sqlite3
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import uuid
import argparse

# Database setup
DB_PATH = os.path.expanduser("~/.blackroad/ocean.db")

class SensorType(Enum):
    BUOY = "buoy"
    ARGO_FLOAT = "argo_float"
    GLIDER = "glider"
    MOORING = "mooring"
    AUV = "auv"
    CTD = "ctd"

@dataclass
class OceanSensor:
    id: str
    name: str
    type: str
    lat: float
    lon: float
    depth_m: float
    status: str
    last_reading_ts: str

@dataclass
class OceanReading:
    sensor_id: str
    temperature_c: float
    salinity_psu: float
    ph: float
    dissolved_o2_mgl: float
    current_ms: float
    depth_m: float
    timestamp: str

class OceanDataCollector:
    def __init__(self):
        self.db_path = DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        self._initialize_demo_sensors()
    
    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS sensors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            depth_m REAL NOT NULL,
            status TEXT NOT NULL,
            last_reading_ts TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            temperature_c REAL NOT NULL,
            salinity_psu REAL NOT NULL,
            ph REAL NOT NULL,
            dissolved_o2_mgl REAL NOT NULL,
            current_ms REAL NOT NULL,
            depth_m REAL NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(sensor_id) REFERENCES sensors(id)
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            type TEXT NOT NULL,
            value REAL NOT NULL,
            severity TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(sensor_id) REFERENCES sensors(id)
        )''')
        
        conn.commit()
        conn.close()
    
    def _initialize_demo_sensors(self):
        """Initialize demo sensors if not already present."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM sensors')
        if c.fetchone()[0] == 0:
            demo_sensors = [
                ('S_PACIFIC_01', 'Pacific Buoy', 'buoy', 35.5, -120.3, 4000, 'active'),
                ('S_ATLANTIC_01', 'Atlantic Mooring', 'mooring', 45.2, -30.1, 5000, 'active'),
                ('S_ARCTIC_01', 'Arctic Glider', 'glider', 78.5, 15.2, 3000, 'active'),
            ]
            
            for sensor_id, name, type_, lat, lon, depth, status in demo_sensors:
                c.execute('''INSERT INTO sensors VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                         (sensor_id, name, type_, lat, lon, depth, status, None))
            
            conn.commit()
        
        conn.close()
    
    def deploy_sensor(self, name: str, type_: str, lat: float, lon: float, depth_m: float) -> OceanSensor:
        """Deploy a new sensor."""
        if type_ not in [t.value for t in SensorType]:
            raise ValueError(f"Invalid type. Must be one of {[t.value for t in SensorType]}")
        
        sensor_id = f"S_{uuid.uuid4().hex[:8].upper()}"
        
        sensor = OceanSensor(
            id=sensor_id,
            name=name,
            type=type_,
            lat=lat,
            lon=lon,
            depth_m=depth_m,
            status="active",
            last_reading_ts=None
        )
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO sensors VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (sensor.id, sensor.name, sensor.type, sensor.lat, sensor.lon, 
                  sensor.depth_m, sensor.status, sensor.last_reading_ts))
        conn.commit()
        conn.close()
        
        return sensor
    
    def ingest_reading(self, sensor_id: str, temp: float, salinity: float, ph: float,
                      o2: float, current: float = 0, depth: Optional[float] = None) -> OceanReading:
        """Ingest a new sensor reading."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get sensor info
        c.execute('SELECT * FROM sensors WHERE id = ?', (sensor_id,))
        sensor_row = c.fetchone()
        if not sensor_row:
            conn.close()
            raise ValueError(f"Sensor {sensor_id} not found")
        
        depth = depth or sensor_row[5]
        timestamp = datetime.now().isoformat()
        
        # Insert reading
        c.execute('''INSERT INTO readings (sensor_id, temperature_c, salinity_psu, ph, dissolved_o2_mgl, current_ms, depth_m, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (sensor_id, temp, salinity, ph, o2, current, depth, timestamp))
        
        # Update sensor last reading
        c.execute('UPDATE sensors SET last_reading_ts = ? WHERE id = ?', (timestamp, sensor_id))
        
        # Check for anomalies
        self._check_anomalies(c, sensor_id, temp, ph, o2, timestamp)
        
        conn.commit()
        conn.close()
        
        return OceanReading(sensor_id, temp, salinity, ph, o2, current, depth, timestamp)
    
    def _check_anomalies(self, cursor, sensor_id: str, temp: float, ph: float, o2: float, timestamp: str):
        """Check for environmental anomalies."""
        if temp > 30:
            cursor.execute('''INSERT INTO anomalies (sensor_id, type, value, severity, timestamp)
                            VALUES (?, ?, ?, ?, ?)''',
                          (sensor_id, 'high_temperature', temp, 'warning', timestamp))
        
        if ph < 7.8:
            cursor.execute('''INSERT INTO anomalies (sensor_id, type, value, severity, timestamp)
                            VALUES (?, ?, ?, ?, ?)''',
                          (sensor_id, 'ocean_acidification', ph, 'critical', timestamp))
        
        if o2 < 4:
            cursor.execute('''INSERT INTO anomalies (sensor_id, type, value, severity, timestamp)
                            VALUES (?, ?, ?, ?, ?)''',
                          (sensor_id, 'hypoxia', o2, 'critical', timestamp))
    
    def get_latest(self, sensor_id: str) -> Optional[OceanReading]:
        """Get latest reading for a sensor."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''SELECT sensor_id, temperature_c, salinity_psu, ph, dissolved_o2_mgl, current_ms, depth_m, timestamp
                    FROM readings WHERE sensor_id = ? ORDER BY timestamp DESC LIMIT 1''', (sensor_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return OceanReading(*row)
    
    def get_history(self, sensor_id: str, hours: int = 24) -> List[OceanReading]:
        """Get reading history."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        c.execute('''SELECT sensor_id, temperature_c, salinity_psu, ph, dissolved_o2_mgl, current_ms, depth_m, timestamp
                    FROM readings WHERE sensor_id = ? AND timestamp > ? ORDER BY timestamp DESC''',
                 (sensor_id, cutoff.isoformat()))
        rows = c.fetchall()
        conn.close()
        
        return [OceanReading(*row) for row in rows]
    
    def fleet_status(self) -> List[Dict]:
        """Get status of all sensors."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT * FROM sensors')
        sensors = c.fetchall()
        
        status_list = []
        for sensor in sensors:
            latest = self.get_latest(sensor[0])
            status_list.append({
                "id": sensor[0],
                "name": sensor[1],
                "type": sensor[2],
                "lat": sensor[3],
                "lon": sensor[4],
                "depth_m": sensor[5],
                "status": sensor[6],
                "last_reading": latest.__dict__ if latest else None
            })
        
        conn.close()
        return status_list
    
    def detect_anomalies(self) -> List[Dict]:
        """Get current anomalies."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Recent anomalies (last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        
        c.execute('''SELECT sensor_id, type, value, severity, timestamp FROM anomalies 
                    WHERE timestamp > ? ORDER BY timestamp DESC''', (cutoff.isoformat(),))
        
        anomalies = []
        for row in c.fetchall():
            anomalies.append({
                "sensor_id": row[0],
                "type": row[1],
                "value": row[2],
                "severity": row[3],
                "timestamp": row[4]
            })
        
        conn.close()
        return anomalies
    
    def calculate_heat_content(self, sensor_ids: List[str]) -> Dict:
        """Calculate integrated ocean heat content."""
        total_heat = 0
        readings_count = 0
        
        for sensor_id in sensor_ids:
            latest = self.get_latest(sensor_id)
            if latest:
                # Simplified heat content estimation
                heat = latest.temperature_c * latest.depth_m * 4186 / 1000  # kJ/m²
                total_heat += heat
                readings_count += 1
        
        return {
            "total_heat_content_kj_m2": round(total_heat, 2),
            "average_heat_kj_m2": round(total_heat / readings_count, 2) if readings_count > 0 else 0,
            "sensors_sampled": readings_count
        }
    
    def export_netcdf_stub(self, output_path: str):
        """Export data as structured JSON mimicking NetCDF."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get all sensors and recent readings
        c.execute('SELECT * FROM sensors')
        sensors = c.fetchall()
        
        netcdf_stub = {
            "dimensions": {
                "time": "unlimited",
                "station": len(sensors)
            },
            "variables": {
                "time": {"units": "seconds since 2020-01-01", "data": []},
                "lat": {"units": "degrees_north", "data": []},
                "lon": {"units": "degrees_east", "data": []},
                "depth": {"units": "meters", "data": []},
                "temperature": {"units": "degC", "data": []},
                "salinity": {"units": "PSU", "data": []},
                "ph": {"units": "pH", "data": []},
                "dissolved_oxygen": {"units": "mg/L", "data": []}
            },
            "metadata": {
                "title": "BlackRoad Ocean Data Collection",
                "source": "Distributed Sensor Network",
                "created": datetime.now().isoformat()
            }
        }
        
        for sensor in sensors:
            latest = self.get_latest(sensor[0])
            if latest:
                netcdf_stub["variables"]["lat"]["data"].append(sensor[3])
                netcdf_stub["variables"]["lon"]["data"].append(sensor[4])
                netcdf_stub["variables"]["depth"]["data"].append(latest.depth_m)
                netcdf_stub["variables"]["temperature"]["data"].append(latest.temperature_c)
                netcdf_stub["variables"]["salinity"]["data"].append(latest.salinity_psu)
                netcdf_stub["variables"]["ph"]["data"].append(latest.ph)
                netcdf_stub["variables"]["dissolved_oxygen"]["data"].append(latest.dissolved_o2_mgl)
        
        conn.close()
        
        with open(output_path, 'w') as f:
            json.dump(netcdf_stub, f, indent=2)
    
    def heatmap_ascii(self, parameter: str = "temperature") -> str:
        """Generate ASCII heatmap of readings."""
        fleet = self.fleet_status()
        
        if not fleet or not any(s["last_reading"] for s in fleet):
            return "No data available"
        
        # Create simple grid
        lats = sorted(set(s["lat"] for s in fleet))
        lons = sorted(set(s["lon"] for s in fleet))
        
        grid = []
        header = "    " + "".join(f"{lon:>6.1f}" for lon in lons)
        grid.append(header)
        
        for lat in reversed(lats):
            row = f"{lat:>3.1f}"
            for lon in lons:
                sensor = next((s for s in fleet if s["lat"] == lat and s["lon"] == lon), None)
                if sensor and sensor["last_reading"]:
                    if parameter == "temperature":
                        val = sensor["last_reading"]["temperature_c"]
                        char = chr(0x2588) if val > 25 else chr(0x2589) if val > 15 else "."
                    elif parameter == "salinity":
                        val = sensor["last_reading"]["salinity_psu"]
                        char = "*" if val > 35 else "o" if val > 33 else "."
                    else:
                        char = "?"
                    row += f"{char:>6}"
                else:
                    row += "     ?"
            grid.append(row)
        
        return "\n".join(grid)
    
    def alert_summary(self) -> str:
        """Generate alert summary."""
        anomalies = self.detect_anomalies()
        
        if not anomalies:
            return "✓ No active anomalies"
        
        summary = f"⚠ {len(anomalies)} anomalies detected:\n"
        
        by_severity = {}
        for anom in anomalies:
            sev = anom["severity"]
            by_severity.setdefault(sev, []).append(anom)
        
        for sev in ["critical", "warning", "info"]:
            if sev in by_severity:
                summary += f"\n  {sev.upper()}:\n"
                for anom in by_severity[sev][:3]:
                    summary += f"    • {anom['type']}: {anom['value']:.2f} ({anom['sensor_id']})\n"
        
        return summary


def main():
    parser = argparse.ArgumentParser(description="Ocean data collection system")
    subparsers = parser.add_subparsers(dest="command")
    
    # Fleet command
    subparsers.add_parser("fleet", help="Show fleet status")
    
    # Anomalies command
    subparsers.add_parser("anomalies", help="Show anomalies")
    
    # Heatmap command
    hm_parser = subparsers.add_parser("heatmap", help="Show heatmap")
    hm_parser.add_argument("parameter", default="temperature", nargs="?")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy sensor")
    deploy_parser.add_argument("name")
    deploy_parser.add_argument("type")
    deploy_parser.add_argument("lat", type=float)
    deploy_parser.add_argument("lon", type=float)
    deploy_parser.add_argument("depth", type=float)
    
    args = parser.parse_args()
    collector = OceanDataCollector()
    
    if args.command == "fleet":
        fleet = collector.fleet_status()
        print(f"✓ Fleet Status ({len(fleet)} sensors):")
        print(json.dumps(fleet, indent=2, default=str))
    
    elif args.command == "anomalies":
        print(collector.alert_summary())
        anomalies = collector.detect_anomalies()
        if anomalies:
            print("\nDetailed anomalies:")
            print(json.dumps(anomalies, indent=2, default=str))
    
    elif args.command == "heatmap":
        print(f"\n{args.parameter.upper()} Heatmap:")
        print(collector.heatmap_ascii(args.parameter))
    
    elif args.command == "deploy":
        sensor = collector.deploy_sensor(args.name, args.type, args.lat, args.lon, args.depth)
        print(f"✓ Deployed: {sensor.id} - {sensor.name}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
