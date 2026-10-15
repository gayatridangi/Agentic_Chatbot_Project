import re
from datetime import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests
from langchain.tools import tool


@tool
def calculator(expression: str) -> str:
    """Calculate basic arithmetic expressions."""

    expression = expression.strip().replace("^", "**")

    if not expression:
        return "Error: expression is empty."

    if len(expression) > 100:
        return "Error: expression is too long."

    if not re.fullmatch(r"[0-9\s+*\-/%().]+", expression):
        return "Error: only basic arithmetic characters are allowed."

    try:
        result = eval(
            expression,
            {"__builtins__": {}},
            {},
        )

    except ZeroDivisionError:
        return "Error: division by zero is not allowed."

    except Exception as exc:
        return f"Error: could not calculate expression ({exc})."

    return str(result)


@tool
def get_current_time(
    timezone: str = "Asia/Kolkata",
) -> str:
    """Return current date and time for an IANA timezone."""

    try:
        now = datetime.now(
            ZoneInfo(timezone)
        )

    except Exception as exc:
        raise ValueError(
            "Invalid timezone. Use an IANA timezone such as Asia/Kolkata or America/New_York."
        ) from exc

    return now.strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )


@tool
def get_weather(city: str) -> str:
    """Return current weather for a city using Open-Meteo."""

    city = city.strip()

    if not city:
        raise ValueError(
            "City name is required."
        )

    geocode_url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={quote(city)}"
        "&count=1"
        "&language=en"
        "&format=json"
    )

    geocode_response = requests.get(
        geocode_url,
        timeout=10,
    )

    geocode_response.raise_for_status()

    geocode_data = geocode_response.json()

    results = geocode_data.get("results") or []

    if not results:
        return f"No location was found for {city}."

    location = results[0]

    latitude = location["latitude"]
    longitude = location["longitude"]

    resolved_name = location.get(
        "name",
        city,
    )

    country = location.get(
        "country",
        "",
    )

    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        "&timezone=auto"
    )

    weather_response = requests.get(
        weather_url,
        timeout=10,
    )

    weather_response.raise_for_status()

    weather_data = weather_response.json()

    current = weather_data["current"]

    units = weather_data.get(
        "current_units",
        {},
    )

    temperature = current.get(
        "temperature_2m"
    )

    humidity = current.get(
        "relative_humidity_2m"
    )

    wind_speed = current.get(
        "wind_speed_10m"
    )

    temperature_unit = units.get(
        "temperature_2m",
        "°C",
    )

    humidity_unit = units.get(
        "relative_humidity_2m",
        "%",
    )

    wind_unit = units.get(
        "wind_speed_10m",
        "km/h",
    )

    return (
        f"Current weather in {resolved_name}, {country}: "
        f"temperature {temperature} {temperature_unit}, "
        f"humidity {humidity} {humidity_unit}, "
        f"wind speed {wind_speed} {wind_unit}."
    )


TOOLS = [
    calculator,
    get_current_time,
    get_weather,
] 
print("hello")