from langchain_core.tools import tool
from langchain_core.runnables.config import RunnableConfig
from datetime import datetime
from src.utils.logger import logger
from src.apis.controllers.scheduling_controller import (
    create_a_activity_controller,
    update_a_activity_controller,
    delete_activities_controller,
    search_activities_controller,
)

@tool
async def create_a_activity(
    description: str,
    activity_category: str,
    start_time: datetime,
    end_time: datetime,
    config: RunnableConfig,
) -> str:
    """Create an activity by extracting details from conversation context if available.
    Note: Call tool when user creates schedule for a single location

    Args:
        description (str): Concise description of the activity. Not too detailing.
        activity_category (str): value in list ["work", "study", "relax", "exercise", "other"] classifying the activity based on user's description. Not required user typing the category, it can be extracted from the description. If not sure then return 'other'.
        start_time (datetime): Activity's start time in the format "YYYY-MM-DD HH:MM:SS".
        end_time (datetime): Activity's end time in the format "YYYY-MM-DD HH:MM:SS".
    """
    try:
        # Convert start_time and end_time to the required format
        configuration = config.get("configurable", {})
        user_id = configuration.get("user_id", None)
        if not user_id:
            logger.warning(f"User not login")
            return "You are not logged in. Please log in to use this feature"
        response = await create_a_activity_controller(
            None,
            activity_category,
            description,
            start_time,
            end_time,
            user_id,
            overlap_allow=False,
        )
        return response["message"]
    except Exception as e:
        logger.error(f"Error creating activity: {e}")
        return f"Error creating activity {e}"


@tool
async def search_activities(
    start_time: datetime,
    end_time: datetime,
    config: RunnableConfig,
) -> str:
    """Search for activities by extracting details from conversation context if available or asking the user for the details.
    Using
    Args:
        start_time (datetime): Activity's start time in the format "YYYY-MM-DD HH:MM:SS". Ask the user for the start time of the activity.
        end_time (datetime): Activity's end time in the format "YYYY-MM-DD HH:MM:SS". Ask the user if they not mentioned the end time of the activity.
    """
    try:
        configuration = config.get("configurable", {})
        user_id = configuration.get("user_id", None)
        if not user_id:
            logger.warning(f"User not login")
            return "You are not logged in. Please log in to use this feature"
        response = await search_activities_controller(start_time, end_time, user_id)
        return response["message"]
    except Exception as e:
        logger.error(f"Error searching activities: {e}")
        return f"Error searching activities {e}"


@tool
async def update_a_activiy(
    description: str,
    activity_category: str,
    start_time: datetime,
    end_time: datetime,
    config: RunnableConfig,
) -> str:
    """Update an activity by extracting details from conversation context if available or asking the user for the details.

    description (str): Concise description of the activity. Not too detailing.
    activity_category (str): value in list ["work", "study", "relax", "exercise", "other"] classifying the activity based on user's description. Not required user typing the category, it can be extracted from the description. If not sure then return 'other'.
    start_time (datetime): Activity's start time in the format "YYYY-MM-DD HH:MM:SS".
    end_time (datetime): Activity's end time in the format "YYYY-MM-DD HH:MM:SS".
    """
    try:
        configuration = config.get("configurable", {})
        user_id = configuration.get("user_id", None)
        if not user_id:
            logger.warning(f"User not login")
            return "You are not logged in. Please log in to use this feature"
        response = await update_a_activity_controller(
            None,
            activity_category,
            description,
            start_time,
            end_time,
            user_id,
        )
        return response["message"]
    except Exception as e:
        logger.error(f"Error updating activity: {e}")
        return f"Error updating activity {e}"


@tool
async def delete_a_activity(
    start_time: datetime,
    end_time: datetime,
    config: RunnableConfig,
) -> str:
    """Delete an activity by extracting details from conversation context if available or asking the user for the details.
    Args:
        start_time (datetime): Activity's start time in the format "YYYY-MM-DD HH:MM:SS".
        end_time (datetime): Activity's end time in the format "YYYY-MM-DD HH:MM:SS".
    """
    try:
        configuration = config.get("configurable", {})
        user_id = configuration.get("user_id", None)
        if not user_id:
            logger.warning(f"User not login")
            return "You are not logged in. Please log in to use this feature"
        response = await delete_activities_controller(
            None, start_time, end_time, user_id
        )
        return response["message"]
    except Exception as e:
        logger.error(f"Error deleting activity: {e}")
        return f"Error deleting activity {e}"
        logger.error(f"Error deleting activity: {e}")
        return f"Error deleting activity {e}"
