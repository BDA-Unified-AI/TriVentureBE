from src.utils.logger import logger
from src.utils.helper import (
    format_geoapify_response,
    format_weather_data,
    get_google_map_url,
)
from fastapi.responses import JSONResponse
import requests
import os
import json


def get_location_details(lat, long):
    api_key = os.getenv("OPENCAGE_API_KEY")
    url = f"https://api.opencagedata.com/geocode/v1/json?q={lat},{long}&pretty=1&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        logger.info("Location details fetched successfully")
        return JSONResponse(
            content={"location": response.json()["results"][0]["formatted"]},
            status_code=200,
        )
    else:
        return JSONResponse(
            content={"error": "Error fetching location details"}, status_code=500
        )


def get_nearby_places(lat, long, radius, kinds):
    api_key = os.getenv("OPENTRIPMAP_API_KEY", None)
    if api_key is None:
        logger.error("OpenTripMap API key not found")
        return JSONResponse(content={"error": "API key not found"}, status=500)
    url = "https://api.opentripmap.com/0.1/en/places/radius"
    params = {
        "radius": radius,
        "lon": long,
        "lat": lat,
        "kinds": kinds,
        "apikey": api_key,
    }
    response = requests.get(url, params=params, headers={"accept": "application/json"})
    if response.status_code == 200:
        logger.info("Places fetched successfully")
        return JSONResponse(
            content={"places": response.json().get("features", [])}, status_code=200
        )
    else:
        return JSONResponse(content={"error": "Error fetching places"}, status_code=500)


def get_places(lat, long, radius, categories, limit=20):
    api_key = os.getenv("GEOAPIFY_API_KEY", None)
    if api_key is None:
        logger.error("Geoapify API key not found")
        return JSONResponse(content={"error": "API key not found"}, status=500)
    url = f"https://api.geoapify.com/v2/places?categories={categories}&filter=circle:{long},{lat},{radius}&limit={limit}&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        response = response.json().get("features", [])
        if response:
            response = format_geoapify_response(response, long, lat)
        return JSONResponse(content=response, status_code=200)
    else:
        return JSONResponse(content={"error": "Error fetching places"}, status_code=500)


def get_weather(lat, long):
    api_key = os.getenv("OPENWEATHER_API_KEY", None)
    if api_key is None:
        logger.error("OpenWeather API key not found")
        return JSONResponse(content={"error": "API key not found"}, status=500)
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={long}&exclude=hourly,daily&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        response = format_weather_data(response.json())
        return JSONResponse(content=response, status_code=200)
    else:
        return JSONResponse(
            content={"error": "Error fetching weather"}, status_code=500
        )


def get_weather_api(destination: str):
    lat, long = get_lat_long_location(destination)
    print("lat", lat, "long", long)
    return json.loads(get_weather(lat, long).body)


def get_lat_long_location(location_name):
    """
    Retrieve the latitude and longitude for a given location name using Geoapify's Geocoding API.

    Parameters:
    - location_name (str): The name of the location to geocode.
    - api_key (str): Your Geoapify API key.

    Returns:
    - tuple: (latitude, longitude) if the location is found; otherwise, (None, None).
    """
    api_key = os.getenv("GEOAPIFY_API_KEY", None)
    base_url = "https://api.geoapify.com/v1/geocode/search"
    params = {"text": location_name, "apiKey": api_key}
    response = requests.get(base_url, params=params)
    data = response.json()
    if response.status_code == 200 and data.get("features"):
        # Extract latitude and longitude from the response
        latitude = data["features"][0]["properties"]["lat"]
        longitude = data["features"][0]["properties"]["lon"]
        return latitude, longitude
    else:
        print(f"Location '{location_name}' not found.")
        return None, None


def get_geometry_nearby_places(lat, lon, radius, kinds):
    res = get_nearby_places(lat=lat, long=lon, radius=radius, kinds=kinds)
    data = json.loads(res.body)
    recommend_places = data.get("places", [])
    recommend_places = [place["properties"]["name"] for place in recommend_places]
    return recommend_places
