# Aliyun MCP Weather Skill

A weather query skill for Aliyun Model Context Protocol (MCP), providing simulated weather data for major Chinese cities.

## Features

- **`get_weather(city)`**: Get weather information for a city
- Returns structured weather data including temperature, condition, humidity, and wind speed
- Supports major Chinese cities: Beijing, Shanghai, Guangzhou, Shenzhen
- Case-insensitive city name matching

## Installation

```bash
pip install aliyun-mcp-weather-skill-20260130
```

## Usage

### Basic Usage

```python
from aliyun_mcp_skill import get_weather

# Get weather for Beijing
weather = get_weather("Beijing")
print(weather)
# Output:
# {
#     "city": "Beijing",
#     "temperature": 22,
#     "condition": "sunny",
#     "humidity": 45,
#     "wind_speed": 10
# }

# Get weather for Shanghai
shanghai_weather = get_weather("shanghai")
print(shanghai_weather)
```

### Aliyun MCP Integration

To use this skill with Aliyun MCP:

1. Install the package in your MCP server environment
2. Register the skill as a tool in your MCP server:

```python
from mcp.server.mcpserver import MCPServer
from aliyun_mcp_skill import get_weather

# Create MCP server
mcp = MCPServer("Aliyun Weather Server")

# Register weather tool
@mcp.tool()
def weather(city: str) -> dict:
    """Get weather information for a city"""
    return get_weather(city)

# Run server
mcp.run(transport="streamable-http", json_response=True)
```

3. Connect your Aliyun LLM application to the MCP server

## Weather Data

The skill provides simulated weather data for the following cities:

| City | Temperature (°C) | Condition | Humidity (%) | Wind Speed (km/h) |
|------|------------------|-----------|--------------|-------------------|
| Beijing | 22 | sunny | 45 | 10 |
| Shanghai | 25 | cloudy | 60 | 8 |
| Guangzhou | 28 | rainy | 75 | 12 |
| Shenzhen | 27 | partly cloudy | 70 | 9 |

## Development

### Build the package

```bash
python -m build
```

### Upload to PyPI

```bash
python -m twine upload dist/*
```

## License

MIT License
