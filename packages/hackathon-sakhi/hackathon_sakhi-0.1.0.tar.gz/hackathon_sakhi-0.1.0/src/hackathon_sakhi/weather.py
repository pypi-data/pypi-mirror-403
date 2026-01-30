#!/usr/bin/env python3
"""
Weather MCP Server for Hackathon Sakhi.

Provides weather data for safety planning.

Environment Variables:
    OPENWEATHER_API_KEY: Your OpenWeatherMap API key (required)
    LOG_LEVEL: Logging level (optional, default: INFO)
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


@dataclass
class WeatherData:
    """Data class for weather information."""
    city: str
    temperature: float
    description: str
    humidity: int
    wind_speed: float
    
    def to_string(self) -> str:
        """Convert weather data to human-readable string."""
        return (f"The weather in {self.city} is currently {self.description} "
                f"with a temperature of {self.temperature}°C. "
                f"Humidity is {self.humidity}% and wind speed is {self.wind_speed} m/s.")


class WeatherServiceInterface(ABC):
    """Abstract interface for weather services."""
    
    @abstractmethod
    def get_weather(self, city: str) -> Optional[WeatherData]:
        """Get weather data for a city."""
        pass


class OpenWeatherMapService(WeatherServiceInterface):
    """OpenWeatherMap API implementation."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_weather(self, city: str) -> Optional[WeatherData]:
        """Fetch weather data from OpenWeatherMap API."""
        try:
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric"
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return WeatherData(
                city=city,
                temperature=data['main']['temp'],
                description=data['weather'][0]['description'],
                humidity=data['main']['humidity'],
                wind_speed=data['wind']['speed']
            )
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching weather data for {city}: {str(e)}")
            return None
        except KeyError as e:
            self.logger.error(f"Unexpected API response format: {str(e)}")
            return None


class WeatherMCPServer:
    """MCP Server for weather services."""
    
    def __init__(self, weather_service: WeatherServiceInterface):
        self.weather_service = weather_service
        self.mcp = FastMCP("hackathon-weather-service")
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.mcp.tool()
        def get_hackathon_weather(city: str) -> str:
            """
            Get the current weather conditions for a specified city.
            Use this tool when the user asks for the weather, temperature, or conditions.

            Args:
                city: The name of the city (e.g., "London", "Tokyo").

            Returns:
                A string with the current weather summary.
            """
            self.logger.info(f"Tool called: get_current_weather({city})")
            
            weather_data = self.weather_service.get_weather(city)
            if weather_data:
                return weather_data.to_string()
            else:
                return f"Sorry, I couldn't fetch weather data for {city}. Please check the city name and try again."
    
    def run(self):
        """Start the MCP server."""
        self.logger.info("Starting Weather MCP Server...")
        self.mcp.run(transport="stdio")


def setup_logging(log_level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def main():
    """Main entry point for the weather MCP server."""
    try:
        # Load environment variables
        load_dotenv()
        
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENWEATHER_API_KEY not found in environment variables. "
                "Please set it: export OPENWEATHER_API_KEY=your_key"
            )
        
        log_level = os.getenv("LOG_LEVEL", "INFO")
        setup_logging(log_level)
        
        # Initialize services
        weather_service = OpenWeatherMapService(api_key)
        server = WeatherMCPServer(weather_service)
        
        # Start server
        server.run()
        
    except Exception as e:
        logging.error(f"Failed to start weather server: {str(e)}")
        raise


if __name__ == "__main__":
    main()
