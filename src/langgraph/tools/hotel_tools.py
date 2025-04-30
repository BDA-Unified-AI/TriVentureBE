from langchain_core.tools import tool
from langchain_core.runnables.config import RunnableConfig
from datetime import datetime
from typing import Optional
from src.apis.controllers.hotel_controller import (
    book_hotel_controller,
    send_booking_confirmation_email,
)
from src.utils.logger import logger

@tool
async def search_hotels(option: str, config: RunnableConfig):
    """
    Call this tool directly to search hotels for the user. No need to require asking for city location.
    Args:
        option (Literal["popular", "basic", "luxury"]): The type of hotel to search for. Options are "popular", "basic", "luxury"

    """

    configuration = config.get("configurable", {})
    lat = configuration.get("lat", None)
    long = configuration.get("long", None)
    # radius = configuration.get("radius", 5000)
    if lat is None or long is None:
        return "Please provide latitude and longitude"
    # response = process_controller_output(
    #     get_places(lat, long, radius, "accommodation", 2)
    # )
    # return format_accommodation_markdown(response)
    return f"search_hotels_{option}"


@tool
async def book_hotel(
    hotel_email: str,
    hotel_name: str,
    address: str,
    phone_number: Optional[str],
    website: Optional[str],
    start_time: Optional[datetime],
    end_time: Optional[datetime],
    config: RunnableConfig,
):
    """
    Call this tool to book a hotel with the email of the hotel. No need require user's email.
    Args:
        hotel_email (str): Hotel booking email
        hotel_name (str): Hotel name
        address (str): Hotel address
        phone_number (Optional[str]): Hotel phone number
        website (Optional[str]): Hotel website
        start_time (datetime): Start time of the booking in the format "YYYY-MM-DDTHH:MM:SS.sss+00:00"
        end_time (datetime): End time of the booking in the format "YYYY-MM-DDTHH:MM:SS.sss+00:00"

    The start_time and end_time are Python `datetime` objects and will be stored as BSON Date objects in MongoDB.

    """
    start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z")

    configuration = config.get("configurable", {})
    user_id = configuration.get("user_id", None)
    if not user_id:
        logger.warning(f"User not login")
        return "User not login. Please login"
    user_email = configuration.get("user_email", None)
    user_contact_number = configuration.get(
        "contact_number", "Does not have contact number"
    )
    hotel_email = "baohtqe170017@fpt.edu.vn"
    response = await book_hotel_controller(
        hotel_email,
        hotel_name,
        address,
        phone_number,
        website,
        start_time_str,
        end_time_str,
        user_id,
    )
    if response["status"] == "error":
        return response["message"]
    send_booking_confirmation_email(
        user_email, user_contact_number, hotel_email, start_time, end_time
    )
    return "Hotel booked successfully"


async def cancel_hotel(
    receiver_email: str,
    room_number: Optional[str],
    reason: Optional[str],
    config: RunnableConfig,
) -> str:
    """
    Call this tool to cancel a hotel booking with the given email.

    Args:
        receiver_email (str): Hotel booking email
        room_number (Optional[str]): Room number
        reason (Optional[str]): Reason for cancellation

    Returns:
        str: Confirmation message of the cancellation request.
    """
    configuration = config.get("configurable", {})
    user_id = configuration.get("user_id", None)
    if not user_id:
        logger.warning(f"User not login")
        return "User not login. Please login"
    if receiver_email is None:
        return "The hotel booking email is required"
    return f"Email sent to {receiver_email} to cancel booking for room {room_number} with reason: {reason}"


@tool
async def update_hotel(
    receiver_email: str,
    room_number: Optional[str],
    content: Optional[str],
    config: RunnableConfig,
):
    """
    Call this tool to update a hotel booking with the given email
    Args:
        receiver_email (str): Hotel booking email
        room_number (Optional[str]): Room number
        content (Optional[str]): Updated content
    """
    configuration = config.get("configurable", {})
    user_id = configuration.get("user_id", None)
    if not user_id:
        logger.warning(f"User not login")
        return "User not login. Please login"
    if receiver_email is None:
        return "The hotel booking email is required"
    return f"Email sent to {receiver_email} to update booking for room {room_number} with content: {content}"
