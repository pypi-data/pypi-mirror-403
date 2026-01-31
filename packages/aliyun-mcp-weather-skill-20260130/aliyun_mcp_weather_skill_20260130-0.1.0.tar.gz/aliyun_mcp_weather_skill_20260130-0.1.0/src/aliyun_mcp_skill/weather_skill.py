"""Weather query skill for Aliyun MCP."""

from typing import Dict, Any

def get_weather(city: str) -> Dict[str, Any]:
    """Get weather information for a city.
    
    Args:
        city: City name to query weather for
        
    Returns:
        Dictionary containing weather information including:
        - city: City name
        - temperature: Current temperature in Celsius
        - condition: Weather condition (e.g., sunny, cloudy)
        - humidity: Humidity percentage
        - wind_speed: Wind speed in km/h
    """
    # Simulated weather data (in a real skill, this would call an API)
    weather_data = {
        "beijing": {
            "temperature": 22,
            "condition": "sunny",
            "humidity": 45,
            "wind_speed": 10
        },
        "shanghai": {
            "temperature": 25,
            "condition": "cloudy",
            "humidity": 60,
            "wind_speed": 8
        },
        "guangzhou": {
            "temperature": 28,
            "condition": "rainy",
            "humidity": 75,
            "wind_speed": 12
        },
        "shenzhen": {
            "temperature": 27,
            "condition": "partly cloudy",
            "humidity": 70,
            "wind_speed": 9
        }
    }
    
    # Convert city name to lowercase for case-insensitive matching
    city_lower = city.lower()
    
    # Get weather data for the city, or return default for unknown cities
    if city_lower in weather_data:
        data = weather_data[city_lower]
    else:
        # Default weather data for unknown cities
        data = {
            "temperature": 20,
            "condition": "unknown",
            "humidity": 50,
            "wind_speed": 5
        }
    
    # Return complete weather information
    return {
        "city": city,
        "temperature": data["temperature"],
        "condition": data["condition"],
        "humidity": data["humidity"],
        "wind_speed": data["wind_speed"]
    }
