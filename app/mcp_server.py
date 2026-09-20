from datetime import datetime, timezone, date, timedelta
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("singapore-travel-current-info")

CITY_COORDS = {"singapore": (1.3521, 103.8198)}

@mcp.tool()
async def get_weather_forecast(city: str = "Singapore", days: int = 3, start_date: str = "today") -> dict[str, Any]:
    """Return current conditions and a daily forecast from Open-Meteo."""
    key = city.strip().lower()
    if key not in CITY_COORDS:
        return {"ok": False, "error": "Weather is configured only for Singapore."}

    days = max(1, min(int(days), 7))
    lat, lon = CITY_COORDS[key]

    # "next_week" means the next Monday in the MCP server's current date.
    # An explicit ISO date is also accepted for deterministic testing.
    if start_date == "next_week":
        today = date.today()
        next_monday = today + timedelta(days=(7 - today.weekday()))
        start_date_value = next_monday.isoformat()
    elif start_date == "today":
        start_date_value = None
    else:
        start_date_value = start_date

    params = {
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "forecast_days": days, "timezone": "Asia/Singapore",
    }
    if start_date_value:
        start = date.fromisoformat(start_date_value)
        params.pop("forecast_days", None)
        params["start_date"] = start.isoformat()
        params["end_date"] = (start + timedelta(days=days - 1)).isoformat()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            response.raise_for_status()
            data = response.json()

        daily = []
        for i, date in enumerate(data.get("daily", {}).get("time", [])):
            daily.append({
                "date": date,
                "weather_code": data["daily"]["weather_code"][i],
                "temp_max_c": data["daily"]["temperature_2m_max"][i],
                "temp_min_c": data["daily"]["temperature_2m_min"][i],
                "precipitation_probability_percent":
                    data["daily"]["precipitation_probability_max"][i],
            })
        return {
            "ok": True,
            "tool": "get_weather_forecast",
            "provider": "Open-Meteo",
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "city": "Singapore",
            "current": data.get("current", {}),
            "daily": daily,
        }
    except Exception as exc:
        return {"ok": False, "tool": "get_weather_forecast",
                "error": f"Weather service unavailable: {exc}"}

@mcp.tool()
async def convert_currency(
    amount: float, from_currency: str, to_currency: str
) -> dict[str, Any]:
    """Convert an amount using Frankfurter exchange-rate data."""
    fc, tc = from_currency.upper(), to_currency.upper()
    if fc == tc:
        return {
            "ok": True, "tool": "convert_currency", "provider": "Frankfurter",
            "amount": amount, "from": fc, "to": tc, "rate": 1.0,
            "converted_amount": amount, "date": datetime.now(timezone.utc).date().isoformat(),
        }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://api.frankfurter.app/latest",
                params={"amount": amount, "from": fc, "to": tc},
            )
            response.raise_for_status()
            data = response.json()
        converted = data.get("rates", {}).get(tc)
        if converted is None:
            return {"ok": False, "tool": "convert_currency",
                    "error": f"No {tc} rate was returned for {fc}."}
        return {
            "ok": True, "tool": "convert_currency", "provider": "Frankfurter",
            "amount": amount, "from": fc, "to": tc,
            "rate": converted / amount if amount else None,
            "converted_amount": converted, "date": data.get("date"),
        }
    except Exception as exc:
        return {"ok": False, "tool": "convert_currency",
                "error": f"Currency service unavailable: {exc}"}

if __name__ == "__main__":
    mcp.run(transport="stdio")
