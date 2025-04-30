from typing import Optional, Dict, Union, List
from datetime import datetime
from src.utils.mongo import ScheduleCRUD
from src.utils.logger import logger
from bson import ObjectId

async def create_a_activity_controller(
    activity_id: Optional[str],
    activity_category: str,
    description: str,
    start_time: datetime,
    end_time: datetime,
    user_id: str,
    overlap_allow: bool = True,
) -> Dict[str, str]:
    try:
        if not overlap_allow:
            existing_activity = await ScheduleCRUD.read_one(
                {
                    "user_id": user_id,
                    "$or": [
                        {
                            "start_time": {"$lte": start_time},
                            "end_time": {"$gt": start_time},
                        },
                        {
                            "start_time": {"$lt": end_time},
                            "end_time": {"$gte": end_time},
                        },
                        {
                            "start_time": {"$gte": start_time},
                            "end_time": {"$lte": end_time},
                        },
                    ],
                }
            )
            if existing_activity:
                activity_category = existing_activity.get("activity_category", "N/A")
                description = existing_activity.get("description", "N/A")
                start_time = existing_activity.get("start_time", "N/A")
                end_time = existing_activity.get("end_time", "N/A")
                return {
                    "status": "error",
                    "message": f"""Overlapping activities found:\nDescription: {description}, \nCategory: {activity_category}, \nStart time: {start_time}, \nEnd time: {end_time}. Please update or delete the existing activity to create a new one.""",
                }
        document = {
            "user_id": user_id,
            "activity_category": activity_category,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
        }
        if activity_id:
            logger.info(f"Create activity with ID: {activity_id}")
            document["id"] = activity_id
        await ScheduleCRUD.create(document)
        return {"status": "success", "message": "Activity created successfully"}

    except Exception as e:
        logger.error(f"Error creating activity: {e}")
        return {"status": "error", "message": f"Error creating activity: {str(e)}"}


async def create_multiple_activities_controller(
    activities: List[Dict],
    user_id: str,
) -> Dict[str, Union[str, List[Dict]]]:
    try:
        results = []

        # Create all activities without checking for overlaps
        for activity in activities:
            activity = activity.model_dump()
            document = {
                "user_id": user_id,
                "activity_category": "AI Trip Planner",
                "description": activity.get("description"),
                "start_time": activity.get("start_time"),
                "end_time": activity.get("end_time"),
            }

            if activity.get("activity_id"):
                document["id"] = activity.get("activity_id")

            created = await ScheduleCRUD.create(document)
            results.append(created)

        return {
            "status": "success",
            "message": f"Successfully created {len(results)} activities",
            "activities": results,
        }

    except Exception as e:
        logger.error(f"Error creating multiple activities: {e}")
        return {
            "status": "error",
            "message": f"Error creating multiple activities: {str(e)}",
        }


async def search_activities_controller(
    start_time: datetime,
    end_time: datetime,
    user_id: str,
) -> Dict[str, Union[str, list[dict]]]:
    try:
        if not start_time or not end_time:
            activities = await ScheduleCRUD.read({"user_id": user_id})
        else:
            activities = await ScheduleCRUD.read(
                {
                    "user_id": user_id,
                    "$or": [
                        {
                            "start_time": {"$lte": start_time},
                            "end_time": {"$gt": start_time},
                        },
                        {
                            "start_time": {"$lt": end_time},
                            "end_time": {"$gte": end_time},
                        },
                        {
                            "start_time": {"$gte": start_time},
                            "end_time": {"$lte": end_time},
                        },
                    ],
                }
            )
        return {"status": "success", "message": activities}
    except Exception as e:
        logger.error(f"Error reading activities: {e}")
        return {"status": "error", "message": f"Error reading activities {e}"}


async def update_a_activity_controller(
    activity_id: Optional[str],
    activity_category: str,
    description: str,
    start_time: datetime,
    end_time: datetime,
    user_id: str,
) -> Dict[str, str]:
    try:
        if activity_id:
            existing_activity = await ScheduleCRUD.read_one(
                {"_id": ObjectId(activity_id)}
            )
            if not existing_activity:
                return {
                    "status": "error",
                    "message": f"Activity with id {activity_id} not found",
                }
        else:
            existing_activity = await ScheduleCRUD.read_one(
                {
                    "user_id": user_id,
                    "$or": [
                        {
                            "start_time": {"$lte": start_time},
                            "end_time": {"$gt": start_time},
                        },
                        {
                            "start_time": {"$lt": end_time},
                            "end_time": {"$gte": end_time},
                        },
                        {
                            "start_time": {"$gte": start_time},
                            "end_time": {"$lte": end_time},
                        },
                    ],
                }
            )
            if not existing_activity:
                return {
                    "status": "error",
                    "message": f"Activity with id {activity_id} not found",
                }
            activity_id = existing_activity["_id"]

        await ScheduleCRUD.update(
            {"_id": ObjectId(activity_id)},
            {
                "activity_category": activity_category,
                "description": description,
                "start_time": start_time,
                "end_time": end_time,
            },
        )
        return {"status": "success", "message": "Activity updated successfully"}
    except Exception as e:
        logger.error(f"Error updating activity: {e}")
        return {"status": "error", "message": f"Error updating activity {e}"}


async def delete_activities_controller(
    activity_id: Optional[str],
    start_time: datetime,
    end_time: datetime,
    user_id: str,
) -> Dict[str, str]:
    try:
        if activity_id:
            existing_activity = await ScheduleCRUD.read_one(
                {"_id": ObjectId(activity_id)}
            )
            if not existing_activity:
                return {
                    "status": "error",
                    "message": "Don't have activity at the given time",
                }
            # Delete single activity by ID
            await ScheduleCRUD.delete({"_id": ObjectId(activity_id)})
            return {"status": "success", "message": "Successfully deleted activity"}
        else:
            # Find all activities in the time range
            existing_activities = await ScheduleCRUD.read(
                {
                    "user_id": user_id,
                    "$or": [
                        {
                            "start_time": {"$lte": start_time},
                            "end_time": {"$gt": start_time},
                        },
                        {
                            "start_time": {"$lt": end_time},
                            "end_time": {"$gte": end_time},
                        },
                        {
                            "start_time": {"$gte": start_time},
                            "end_time": {"$lte": end_time},
                        },
                    ],
                }
            )

            if not existing_activities:
                return {
                    "status": "error",
                    "message": "Don't have any activities at the given time range",
                }

            logger.info(f"Found {len(existing_activities)} activities to delete")

            # Delete all activities in the time range
            await ScheduleCRUD.delete(
                {
                    "user_id": user_id,
                    "$or": [
                        {
                            "start_time": {"$lte": start_time},
                            "end_time": {"$gt": start_time},
                        },
                        {
                            "start_time": {"$lt": end_time},
                            "end_time": {"$gte": end_time},
                        },
                        {
                            "start_time": {"$gte": start_time},
                            "end_time": {"$lte": end_time},
                        },
                    ],
                }
            )

            return {
                "status": "success",
                "message": f"Successfully deleted {len(existing_activities)} activities",
            }

    except Exception as e:
        logger.error(f"Error deleting activities: {e}")
        return {"status": "error", "message": f"Error deleting activities: {e}"}
