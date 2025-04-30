from langchain_core.tools import tool
from src.apis.controllers.destination_controller import (
    destination_recommendation_func,
)
from langchain_core.runnables.config import RunnableConfig
from src.utils.logger import logger
from src.apis.controllers.location_controller import get_weather_api


@tool
async def destination_suggestion(query: str, config: RunnableConfig):
    """Call tool when user want to recommend a travel destination(tourist attractions, restaurants). Not require user typing anything.
    Args:
    query (str): query related to wanting to go somewhere locations near a certain area/location or location's characteristics user want to go. Auto extracted from user's message.
    Using Vietnamese language for better results
    """
    configuration = config.get("configurable", {})
    user_id = configuration.get("user_id", None)
    if not user_id:
        logger.info("User ID is not provided")

    logger.info(f"Destination recommendation query: {query}")
    response = await destination_recommendation_func(query, user_id, tool_chat=True)
    logger.info(f"Destination recommendation output: {response}")
    return response


@tool
def get_weather(destination: str):
    """
    Get weather information for a specific destination.
    Args:
        destination (str): The destination to get weather information for.
    Returns:
        str: Weather information for the destination.
    """
    return get_weather_api(destination)
