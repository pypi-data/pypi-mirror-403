#!/usr/bin/env python3
"""
Location Monitor MCP Server - PyPI Version
This replaces the old location.py in the hackathon-sakhi package.

Works with the Render-hosted FastAPI backend.

Environment Variables:
    LOCATION_API_URL: URL of the hosted API (default: https://sakhi-location-api.onrender.com)
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json

import requests
from mcp.server.fastmcp import FastMCP

# Configuration
DEFAULT_API_URL = "https://sakhi-location-api.onrender.com"

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@dataclass
class LocationSnapshot:
    timestamp: datetime
    battery: int
    network: bool
    lat: float
    lng: float
    local_id: Optional[int] = None


@dataclass
class EmergencyAlert:
    alert_type: str
    severity: str
    message: str
    location: Dict[str, float]
    timestamp: datetime


class LocationAPIClient:
    """Client for the hosted Location API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.timeout = 30
        logger.info(f"Location API: {self.base_url}")
    
    def _request(self, endpoint: str) -> Optional[dict]:
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API error: {e}")
            return None
    
    def get_snapshots(self, hours: int = 24, limit: int = 100) -> List[LocationSnapshot]:
        data = self._request(f"/snapshots/recent?hours={hours}&limit={limit}")
        if not data:
            return []
        
        snapshots = []
        for item in data:
            try:
                ts = datetime.fromisoformat(item['timestamp'].replace('Z', ''))
                snapshots.append(LocationSnapshot(
                    timestamp=ts,
                    battery=item['battery'],
                    network=item['network'],
                    lat=item['lat'],
                    lng=item['lng'],
                    local_id=item.get('local_id')
                ))
            except Exception:
                pass
        return snapshots
    
    def get_status(self) -> Dict[str, Any]:
        data = self._request("/status")
        return data if data else {"status": "error", "message": "Could not connect"}
    
    def health_check(self) -> bool:
        data = self._request("/health")
        return data is not None


class EmergencyDetector:
    THRESHOLDS = {
        "battery_critical": 10,
        "battery_low": 20,
        "timeout_minutes": 30,
    }
    
    def check(self, snapshots: List[LocationSnapshot]) -> List[EmergencyAlert]:
        if not snapshots:
            return []
        
        alerts = []
        latest = snapshots[0]
        
        if latest.battery <= self.THRESHOLDS['battery_critical']:
            alerts.append(EmergencyAlert(
                alert_type="BATTERY_CRITICAL",
                severity="CRITICAL",
                message=f"Battery critically low at {latest.battery}%!",
                location={"lat": latest.lat, "lng": latest.lng},
                timestamp=latest.timestamp
            ))
        elif latest.battery <= self.THRESHOLDS['battery_low']:
            alerts.append(EmergencyAlert(
                alert_type="BATTERY_LOW",
                severity="HIGH",
                message=f"Battery low at {latest.battery}%",
                location={"lat": latest.lat, "lng": latest.lng},
                timestamp=latest.timestamp
            ))
        
        if not latest.network:
            alerts.append(EmergencyAlert(
                alert_type="NETWORK_LOST",
                severity="MEDIUM",
                message="Device lost network connectivity",
                location={"lat": latest.lat, "lng": latest.lng},
                timestamp=latest.timestamp
            ))
        
        mins_since = (datetime.now() - latest.timestamp).total_seconds() / 60
        if mins_since > self.THRESHOLDS['timeout_minutes']:
            alerts.append(EmergencyAlert(
                alert_type="LOCATION_TIMEOUT",
                severity="HIGH",
                message=f"No update for {mins_since:.0f} minutes",
                location={"lat": latest.lat, "lng": latest.lng},
                timestamp=latest.timestamp
            ))
        
        return alerts


# MCP Server
mcp = FastMCP("hackathon-location-monitor")
_client: Optional[LocationAPIClient] = None
_detector = EmergencyDetector()


def _get_client() -> LocationAPIClient:
    global _client
    if _client is None:
        url = os.getenv("LOCATION_API_URL", DEFAULT_API_URL)
        _client = LocationAPIClient(url)
    return _client


@mcp.tool()
def get_hackathon_recent_snapshots(limit: int = 10, hours_back: int = 24) -> str:
    """
    Get recent location snapshots from the tracked device.
    
    Args:
        limit: Maximum number of snapshots (default 10)
        hours_back: Hours to look back (default 24)
        
    Returns:
        JSON with location snapshots including timestamp, battery, network, coordinates
    """
    client = _get_client()
    snapshots = client.get_snapshots(hours=hours_back, limit=limit)
    
    result = {
        "snapshots": [
            {
                "timestamp": s.timestamp.isoformat(),
                "battery": s.battery,
                "network": s.network,
                "location": {"lat": s.lat, "lng": s.lng}
            }
            for s in snapshots
        ],
        "count": len(snapshots),
        "latest": snapshots[0].timestamp.isoformat() if snapshots else None
    }
    return json.dumps(result, indent=2)


@mcp.tool()
def check_hackathon_emergency_conditions() -> str:
    """
    Check if device status indicates emergency conditions.
    
    Analyzes battery, network, and location updates to detect:
    - Battery critically low
    - Network lost
    - No recent location updates
    
    Returns:
        JSON with emergency analysis and alerts
    """
    client = _get_client()
    snapshots = client.get_snapshots(hours=2, limit=10)
    alerts = _detector.check(snapshots)
    status = client.get_status()
    
    result = {
        "emergency_detected": len(alerts) > 0,
        "alerts": [
            {
                "type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "location": a.location
            }
            for a in alerts
        ],
        "status": status
    }
    return json.dumps(result, indent=2)


@mcp.tool()
def get_hackathon_device_status() -> str:
    """
    Get current device status (battery, network, last location).
    
    Returns:
        JSON with device status summary
    """
    client = _get_client()
    status = client.get_status()
    return json.dumps(status, indent=2)


def main():
    """Entry point"""
    logger.info("Starting Location Monitor MCP Server...")
    client = _get_client()
    if client.health_check():
        logger.info(f"✓ Connected to {client.base_url}")
    else:
        logger.warning(f"⚠ Cannot connect to {client.base_url} (may be cold starting)")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
