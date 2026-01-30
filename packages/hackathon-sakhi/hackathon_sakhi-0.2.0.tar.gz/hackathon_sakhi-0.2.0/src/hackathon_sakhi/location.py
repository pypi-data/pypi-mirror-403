#!/usr/bin/env python3
"""
Location Monitor MCP Server for Hackathon Sakhi.

Monitors device location, battery, and network status for safety.

Environment Variables:
    FASTAPI_BASE_URL: URL of the location tracking backend (required)
    LOG_LEVEL: Logging level (optional, default: INFO)
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


@dataclass
class LocationSnapshot:
    """Data class for location snapshot."""
    timestamp: datetime
    battery: int
    network: bool
    lat: float
    lng: float
    local_id: Optional[int] = None


@dataclass
class EmergencyAlert:
    """Data class for emergency alerts."""
    alert_type: str
    severity: str
    message: str
    location: Dict[str, float]
    timestamp: datetime


class LocationServiceInterface(ABC):
    """Abstract interface for location services."""
    
    @abstractmethod
    def get_recent_snapshots(self, limit: int, hours_back: int) -> List[LocationSnapshot]:
        """Get recent location snapshots."""
        pass
    
    @abstractmethod
    def get_device_status(self) -> Dict[str, Any]:
        """Get current device status."""
        pass


class FastAPILocationService(LocationServiceInterface):
    """FastAPI backend location service implementation."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_recent_snapshots(self, limit: int, hours_back: int) -> List[LocationSnapshot]:
        """Fetch recent snapshots from FastAPI server."""
        try:
            response = requests.get(f"{self.base_url}/snapshots", timeout=10)
            response.raise_for_status()
            snapshots_data = response.json()
            
            # Filter by time
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_snapshots = []
            
            for snap in snapshots_data:
                timestamp = datetime.fromisoformat(snap['timestamp'].replace('Z', ''))
                if timestamp > cutoff_time:
                    recent_snapshots.append(LocationSnapshot(
                        timestamp=timestamp,
                        battery=snap['battery'],
                        network=snap['network'],
                        lat=snap['lat'],
                        lng=snap['lng'],
                        local_id=snap.get('local_id')
                    ))
            
            # Sort by timestamp and limit
            recent_snapshots.sort(key=lambda x: x.timestamp, reverse=True)
            return recent_snapshots[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching snapshots: {str(e)}")
            return []
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get current device status."""
        try:
            snapshots = self.get_recent_snapshots(1, 24)
            if not snapshots:
                return {"status": "no_data", "message": "No snapshots available"}
            
            latest = snapshots[0]
            minutes_since = (datetime.now() - latest.timestamp).total_seconds() / 60
            
            return {
                "battery_level": latest.battery,
                "network_connected": latest.network,
                "last_location": {"lat": latest.lat, "lng": latest.lng},
                "last_update": latest.timestamp.isoformat(),
                "minutes_since_update": round(minutes_since, 1),
                "status": "active" if minutes_since < 30 else "stale"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting device status: {str(e)}")
            return {"status": "error", "message": str(e)}


class EmergencyDetector:
    """Detects emergency conditions from location data."""
    
    THRESHOLDS = {
        "battery_low": 15,
        "location_timeout_minutes": 30,
        "network_timeout_minutes": 60
    }
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def check_emergency_conditions(self, snapshots: List[LocationSnapshot]) -> List[EmergencyAlert]:
        """Check for emergency conditions."""
        if not snapshots:
            return []
        
        alerts = []
        latest = snapshots[0]
        
        # Battery check
        if latest.battery <= self.THRESHOLDS['battery_low']:
            alerts.append(EmergencyAlert(
                alert_type="BATTERY_LOW",
                severity="HIGH",
                message=f"Battery critically low: {latest.battery}%",
                location={"lat": latest.lat, "lng": latest.lng},
                timestamp=latest.timestamp
            ))
        
        # Network check
        if not latest.network:
            alerts.append(EmergencyAlert(
                alert_type="NETWORK_LOST",
                severity="MEDIUM", 
                message="Device has lost network connectivity",
                location={"lat": latest.lat, "lng": latest.lng},
                timestamp=latest.timestamp
            ))
        
        # Location timeout check
        minutes_since = (datetime.now() - latest.timestamp).total_seconds() / 60
        if minutes_since > self.THRESHOLDS['location_timeout_minutes']:
            alerts.append(EmergencyAlert(
                alert_type="LOCATION_TIMEOUT",
                severity="HIGH",
                message=f"No location update for {minutes_since:.1f} minutes",
                location={"lat": latest.lat, "lng": latest.lng},
                timestamp=latest.timestamp
            ))
        
        return alerts


class LocationMonitorMCP:
    """MCP Server for location monitoring."""
    
    def __init__(self, location_service: LocationServiceInterface):
        self.location_service = location_service
        self.emergency_detector = EmergencyDetector()
        self.mcp = FastMCP("hackathon-location-monitor")
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.mcp.tool()
        def get_hackathon_recent_snapshots(limit: int = 10, hours_back: int = 24) -> str:
            """
            Get recent location snapshots from device.
            
            Args:
                limit: Number of recent snapshots to retrieve
                hours_back: Hours back to look for snapshots
                
            Returns:
                JSON string with snapshots data
            """
            self.logger.info(f"Tool called: get_hackathon_recent_snapshots(limit={limit}, hours_back={hours_back})")
            
            snapshots = self.location_service.get_recent_snapshots(limit, hours_back)
            
            result = {
                "snapshots": [
                    {
                        "timestamp": snap.timestamp.isoformat(),
                        "battery": snap.battery,
                        "network": snap.network,
                        "location": {"lat": snap.lat, "lng": snap.lng}
                    }
                    for snap in snapshots
                ],
                "count": len(snapshots),
                "latest_timestamp": snapshots[0].timestamp.isoformat() if snapshots else None
            }
            
            return str(result)
        
        @self.mcp.tool()
        def check_hackathon_emergency_conditions(planned_route: str = "") -> str:
            """
            Check if current device status triggers emergency conditions.
            
            Args:
                planned_route: Expected route or destination
                
            Returns:
                JSON string with emergency analysis
            """
            self.logger.info(f"Tool called: check_hackathon_emergency_conditions")
            
            snapshots = self.location_service.get_recent_snapshots(5, 2)
            alerts = self.emergency_detector.check_emergency_conditions(snapshots)
            
            result = {
                "emergency_detected": len(alerts) > 0,
                "alert_count": len(alerts),
                "alerts": [
                    {
                        "type": alert.alert_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "location": alert.location,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in alerts
                ],
                "current_status": self.location_service.get_device_status(),
                "planned_route": planned_route
            }
            
            return str(result)
        
        @self.mcp.tool()
        def get_hackathon_device_status() -> str:
            """
            Get current device status (battery, network, last location).
            
            Returns:
                JSON string with device status
            """
            self.logger.info(f"Tool called: get_hackathon_device_status")
            
            status = self.location_service.get_device_status()
            return str(status)
    
    def run(self):
        """Start the MCP server."""
        self.logger.info("Starting Location Monitor MCP Server...")
        self.mcp.run(transport="stdio")


def setup_logging(log_level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def main():
    """Main entry point for the location monitor MCP server."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Default to Render-hosted backend
        fastapi_url = os.getenv("FASTAPI_BASE_URL", "https://sakhi-location-api.onrender.com")
        
        log_level = os.getenv("LOG_LEVEL", "INFO")
        setup_logging(log_level)
        
        # Initialize services
        location_service = FastAPILocationService(fastapi_url)
        server = LocationMonitorMCP(location_service)
        
        # Start server
        server.run()
        
    except Exception as e:
        logging.error(f"Failed to start location monitor server: {str(e)}")
        raise


if __name__ == "__main__":
    main()
