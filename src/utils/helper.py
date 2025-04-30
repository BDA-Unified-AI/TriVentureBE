from fastapi.responses import JSONResponse
import json
import math
import traceback
from datetime import datetime, timezone
import re
from src.utils.logger import logger
from pydantic import BaseModel, Field
from typing import List, Union
import httpx
from fastapi import HTTPException
from bson import ObjectId


def handle_validator_raise(func):
    """
    Custom decorator to handle exceptions raised by the validator
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if len(traceback.extract_tb(e.__traceback__)) > 1:
                tb = traceback.extract_tb(e.__traceback__)[1]
            else:
                tb = traceback.extract_tb(e.__traceback__)[0]
            filename, lineno, function, line = tb.filename, tb.lineno, tb.name, tb.line
            error_type, error_msg = type(e).__name__, str(e)
            error_info = {
                "error": error_type,
                "message": error_msg,
                "step": function,
                "line": line,
                "filename": filename,
                "lineno": lineno,
            }
            logger.error(f"Exception: {error_info}")

    return wrapper


def process_controller_output(ouput: JSONResponse):
    if ouput.status_code in [
        200,
        201,
    ]:
        return json.loads(ouput.body.decode("utf-8"))
    else:
        return "Error"


def format_weather_data(weather_data):
    try:
        current_weather = weather_data["current"]
        lat = weather_data["lat"]
        lon = weather_data["lon"]
        location = f"Latitude: {lat}, Longitude: {lon}"
        icon_url = f"http://openweathermap.org/img/wn/{current_weather['weather'][0]['icon']}@2x.png"
        formatted_weather = f"In {location}, the current weather is as follows:\n"
        formatted_weather += (
            f"  <img src='{icon_url}' width='100' height='100'/>\n"
        )
        formatted_weather += (
            f"  Detailed status: {current_weather['weather'][0]['description']}\n"
        )
        formatted_weather += f"Wind speed: {current_weather['wind_speed']} m/s, direction: {current_weather['wind_deg']}°\n"
        formatted_weather += f"Humidity: {current_weather['humidity']}%\n"
        formatted_weather += f"Temperature:\n"
        formatted_weather += f"  - Current: {current_weather['temp'] - 273.15:.2f}°C\n"
        formatted_weather += (
            f"  - Feels like: {current_weather['feels_like'] - 273.15:.2f}°C\n"
        )
        if "rain" in current_weather:
            formatted_weather += f"Rain: {current_weather['rain'].get('1h', 0)} mm\n"
        else:
            formatted_weather += "Rain: {}\n"
        formatted_weather += f"Cloud cover: {current_weather['clouds']}%\n"
        return formatted_weather
    except Exception as e:
        return f"Error formatting weather data: {e}"


def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    R = 6371.0
    distance = R * c
    return distance


def format_geoapify_response(
    response, current_long, current_lat, include_latnlong=False
):
    formatted_data = []
    for feature in response:
        formatted_item = {}
        place_lat = feature["geometry"]["coordinates"][1]
        place_lon = feature["geometry"]["coordinates"][0]

        distance = haversine(current_long, current_lat, place_lon, place_lat)
        if include_latnlong:
            formatted_item["lat"] = place_lat
            formatted_item["lon"] = place_lon
        formatted_item["name"] = feature["properties"]["address_line1"]
        formatted_item["address"] = feature["properties"]["formatted"]
        formatted_item["distance_km"] = str(round(distance, 2)) + " km"

        if "contact" in feature["properties"]:
            formatted_item["contact"] = feature["properties"]["contact"]

        if "website" in feature["properties"]:
            formatted_item["website"] = feature["properties"]["website"]

        if "accommodation" in feature["properties"]:
            formatted_item["accommodation"] = feature["properties"]["accommodation"]
        formatted_item["map_url"] = get_google_map_url(place_lat, place_lon)

        formatted_data.append(formatted_item)

    return formatted_data


def format_accommodation_markdown(data):
    formatted = ""
    for entry in data:
        formatted += f"### {entry['Accommodation Name']}\n"
        formatted += f"- **Address:** {entry['Address']}\n"
        formatted += f"- **Distance from center:** {entry['distance_km']}\n"

        contact_info = entry.get("contact")
        if contact_info:
            formatted += "- **Contact:**\n"
            if "phone" in contact_info:
                formatted += f"  - Phone: {contact_info['phone']}\n"
            if "email" in contact_info:
                formatted += f"  - Email: {contact_info['email']}\n"

        if "website" in entry:
            formatted += f"- **Website:** [{entry['website']}]({entry['website']})\n"

        accommodation_info = entry.get("accommodation")
        if accommodation_info:
            formatted += "- **Accommodation Info:**\n"
            if "stars" in accommodation_info:
                formatted += f"  - Stars: {accommodation_info['stars']}\n"
            if "rooms" in accommodation_info:
                formatted += f"  - Rooms: {accommodation_info['rooms']}\n"

        formatted += "\n---\n\n"

    return formatted


@handle_validator_raise
def convert_string_date_to_iso(input_str: str):
    if not input_str:
        raise ValueError("Input date string cannot be empty")
    try:
        # Try parsing with timezone information
        try:
            converted_datetime = datetime.strptime(
                input_str.strip(), "%Y-%m-%dT%H:%M:%S%z"
            )
        except ValueError:
            # If parsing fails, assume UTC timezone
            converted_datetime = datetime.strptime(
                input_str.strip(), "%Y-%m-%dT%H:%M:%S"
            )
            converted_datetime = converted_datetime.replace(tzinfo=None)

        raw_datetime = datetime(
            year=converted_datetime.year,
            month=converted_datetime.month,
            day=converted_datetime.day,
            hour=converted_datetime.hour,
            minute=converted_datetime.minute,
            second=converted_datetime.second,
            tzinfo=converted_datetime.tzinfo,
        )
        return raw_datetime
    except ValueError as e:
        raise ValueError(
            f"Invalid date format. Expected format: YYYY-MM-DDThh:mm:ss+hh:mm or YYYY-MM-DDThh:mm:ss, got: {input_str}"
        )
    except Exception as e:
        raise ValueError(f"Error converting date string: {str(e)}")


@handle_validator_raise
def datetime_to_iso_string(dt: datetime) -> str:
    """Convert a datetime object to a string in the format YYYY-MM-DDTHH:MM:SS.

    Args:
        dt (datetime): The datetime object to convert.

    Returns:
        str: The formatted datetime string.
    """
    converted_datetime = dt.strftime("%Y-%m-%dT%H:%M:%S")
    return converted_datetime


def parse_itinerary(text):
    # Split the input text by date pattern
    days = re.split(r"(\d{2}/\d{2}/\d{4})", text)

    # Initialize an empty list to store each day's activities
    itinerary = []

    # Define a regex to capture the "Additional information" section
    additional_info_pattern = re.compile(r"Additional information:(.*)", re.DOTALL)
    additional_info_match = additional_info_pattern.search(text)

    # If "Additional information" exists, capture it
    additional_info = (
        additional_info_match.group(1).strip() if additional_info_match else ""
    )

    # Loop through the days to extract date and activities
    for i in range(1, len(days), 2):  # Skip even indexes as they are not dates
        date = days[i].strip()
        activities_text = days[i + 1].strip()

        # Find activities
        activities = []
        activity_matches = re.findall(
            r"\((\d{1,2}:\d{2}) - (\d{1,2}:\d{2})\):\s*(.+)", activities_text
        )
        for match in activity_matches:
            start_time, end_time, description = match
            activities.append(
                {
                    "start_time": start_time,
                    "end_time": end_time,
                    "description": description,
                }
            )

        # Append the day's activities to the itinerary
        itinerary.append({"date": date, "activities": activities})

    # Return the itinerary along with the additional information as a string
    return {"itinerary": itinerary, "additional_info": additional_info}


class Destination(BaseModel):
    id: int = Field(..., title="Destination Id", gt=0)
    name: str = Field(..., title="Destination Name", min_length=1)
    location: str = Field(..., title="Location", min_length=1)
    description: str = Field(..., title="Description", min_length=1)


def format_include_destinations(include_destinations: List[Union[Destination, str]]):
    formatted_string = ""
    if not include_destinations:
        return "No destinations required"
    elif all(
        isinstance(destination, Destination) for destination in include_destinations
    ):
        for index, destination in enumerate(include_destinations):
            formatted_string += f"#Destination {int(index) + 1}: {destination.name}\n"
            formatted_string += f" Location: {destination.location}\n"
            formatted_string += f" Description: {destination.description}\n\n"
    else:
        for index, destination in enumerate(include_destinations):
            formatted_string += f"#Destination {int(index) + 1}: {destination}\n"


async def call_external_api(
    method: str,
    url: str,
    headers: dict = None,
    params: dict = None,
    data: dict = None,
    json: dict = None,
    timeout: int = 10,
):
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json,
            )
            response.raise_for_status()  # Raise an error for non-2xx/3xx responses
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj


def get_google_map_url(lat, long):
    return f"https://www.google.com/maps/search/{lat},{long}"
