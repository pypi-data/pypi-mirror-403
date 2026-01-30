import asyncio
import logging
import aiohttp
import time
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Weather data structure."""
    temperature: float  # Celsius
    humidity: float  # Percentage
    pressure: float  # hPa
    wind_speed: float  # m/s
    wind_direction: int  # degrees
    description: str
    timestamp: int
    location: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'temperature': self.temperature,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'description': self.description,
            'timestamp': self.timestamp,
            'location': self.location
        }


class WeatherService:
    """
    Service for fetching weather data from API.

    Supports multiple weather API providers:
    - OpenWeatherMap (recommended, free tier: 1000 calls/day)
    - WeatherAPI (free tier: 1M calls/month)
    """

    def __init__(
        self,
        api_key: str,
        location: str,
        provider: str = "openweathermap",
        update_interval: int = 600,  # 10 minutes default
        cache_duration: int = 300  # Cache for 5 minutes
    ):
        """
        Initialize weather service.

        Args:
            api_key: API key for weather service
            location: Location (city name, coordinates, etc.)
            provider: API provider ('openweathermap' or 'weatherapi')
            update_interval: How often to fetch weather data (seconds)
            cache_duration: How long to cache weather data (seconds)
        """
        self.api_key = api_key
        self.location = location
        self.provider = provider.lower()
        self.update_interval = update_interval
        self.cache_duration = cache_duration

        self.current_weather: Optional[WeatherData] = None
        self.last_update_time: Optional[float] = None
        self.fetch_failures = 0
        self.stop_event = asyncio.Event()

        # API endpoints
        self.api_urls = {
            'openweathermap': 'https://api.openweathermap.org/data/2.5/weather',
            'weatherapi': 'http://api.weatherapi.com/v1/current.json'
        }

        if self.provider not in self.api_urls:
            raise ValueError(f"Unsupported provider: {provider}")

    async def fetch_weather(self) -> Optional[WeatherData]:
        """
        Fetch current weather data from API.

        Returns:
            WeatherData object or None if failed
        """
        # Check cache
        if self.current_weather and self.last_update_time:
            if time.time() - self.last_update_time < self.cache_duration:
                logger.debug(f"Returning cached weather data (age: {time.time() - self.last_update_time:.1f}s)")
                return self.current_weather

        try:
            async with aiohttp.ClientSession() as session:
                if self.provider == 'openweathermap':
                    weather_data = await self._fetch_openweathermap(session)
                elif self.provider == 'weatherapi':
                    weather_data = await self._fetch_weatherapi(session)
                else:
                    return None

                if weather_data:
                    self.current_weather = weather_data
                    self.last_update_time = time.time()
                    self.fetch_failures = 0
                    logger.info(
                        f"✓ Weather updated: {weather_data.temperature}°C, "
                        f"{weather_data.humidity}% humidity, {weather_data.description}"
                    )
                    return weather_data

        except Exception as e:
            self.fetch_failures += 1
            logger.error(f"Failed to fetch weather data: {e} (failure count: {self.fetch_failures})")

        return None

    async def _fetch_openweathermap(self, session: aiohttp.ClientSession) -> Optional[WeatherData]:
        """Fetch from OpenWeatherMap API."""
        params = {
            'q': self.location,
            'appid': self.api_key,
            'units': 'metric'
        }

        async with session.get(self.api_urls['openweathermap'], params=params) as response:
            if response.status != 200:
                logger.error(f"OpenWeatherMap API error: {response.status}")
                return None

            data = await response.json()

            return WeatherData(
                temperature=data['main']['temp'],
                humidity=data['main']['humidity'],
                pressure=data['main']['pressure'],
                wind_speed=data['wind']['speed'],
                wind_direction=data['wind'].get('deg', 0),
                description=data['weather'][0]['description'],
                timestamp=int(time.time()),
                location=self.location
            )

    async def _fetch_weatherapi(self, session: aiohttp.ClientSession) -> Optional[WeatherData]:
        """Fetch from WeatherAPI."""
        params = {
            'key': self.api_key,
            'q': self.location,
            'aqi': 'no'
        }

        async with session.get(self.api_urls['weatherapi'], params=params) as response:
            if response.status != 200:
                logger.error(f"WeatherAPI error: {response.status}")
                return None

            data = await response.json()
            current = data['current']

            return WeatherData(
                temperature=current['temp_c'],
                humidity=current['humidity'],
                pressure=current['pressure_mb'],
                wind_speed=current['wind_kph'] / 3.6,  # Convert to m/s
                wind_direction=current['wind_degree'],
                description=current['condition']['text'],
                timestamp=int(time.time()),
                location=self.location
            )

    async def start_monitoring(self):
        """Start continuous weather monitoring task."""
        logger.info(
            f"Starting weather monitoring service for {self.location} "
            f"(provider: {self.provider}, interval: {self.update_interval}s)"
        )

        # Initial fetch
        await self.fetch_weather()

        # Periodic updates
        while not self.stop_event.is_set():
            try:
                await asyncio.sleep(self.update_interval)
                await self.fetch_weather()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in weather monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def stop(self):
        """Stop weather monitoring."""
        self.stop_event.set()
        logger.info("Weather monitoring service stopped")

    def get_current_weather(self) -> Optional[Dict[str, Any]]:
        """
        Get current cached weather data.

        Returns:
            Dict with weather data or None if not available
        """
        if not self.current_weather:
            return None

        data = self.current_weather.to_dict()
        data['age_seconds'] = time.time() - self.last_update_time if self.last_update_time else None
        data['fetch_failures'] = self.fetch_failures

        return data

    def is_data_fresh(self, max_age_seconds: int = None) -> bool:
        """
        Check if cached weather data is fresh.

        Args:
            max_age_seconds: Maximum acceptable age (defaults to cache_duration)

        Returns:
            True if data is fresh
        """
        if not self.current_weather or not self.last_update_time:
            return False

        max_age = max_age_seconds or self.cache_duration
        age = time.time() - self.last_update_time
        return age < max_age


# Example usage and setup instructions
"""
To use this service, you'll need a free API key:

Option 1: OpenWeatherMap (Recommended)
1. Sign up at: https://openweathermap.org/api
2. Free tier: 1,000 calls/day (plenty for 10-minute updates)
3. Get your API key from the dashboard

Option 2: WeatherAPI
1. Sign up at: https://www.weatherapi.com/
2. Free tier: 1,000,000 calls/month
3. Get your API key from the dashboard

Add to communication.yaml:
```yaml
weather_config:
  provider: "openweathermap"  # or "weatherapi"
  api_key: "your_api_key_here"
  location: "Jodhpur,IN"  # City name or coordinates
  update_interval: 600  # 10 minutes
```

Usage in main.py:
```python
from src.services.weather_service import WeatherService

# Initialize
weather_service = WeatherService(
    api_key=config['weather_config']['api_key'],
    location=config['weather_config']['location'],
    provider=config['weather_config']['provider'],
    update_interval=config['weather_config']['update_interval']
)

# Start monitoring
await weather_service.start_monitoring()

# Get current weather
weather = weather_service.get_current_weather()
if weather:
    print(f"Temperature: {weather['temperature']}°C")
    print(f"Humidity: {weather['humidity']}%")
```
"""
