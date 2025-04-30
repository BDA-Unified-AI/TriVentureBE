from typing import Dict
from datetime import datetime
from src.utils.mongo import ReactionCRUD, PostCRUD
from src.utils.logger import logger
from datetime import datetime
from datetime import datetime
from bson import ObjectId
from src.utils.mongo import UserCRUD
from asyncio import gather


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj


async def create_a_reaction_controller(user_id: str, post_id: str, type: int) -> Dict:
    try:
        reaction = {
            "user_id": user_id,
            "post_id": post_id,
            "type": type,
        }
        await ReactionCRUD.create(reaction)
        await PostCRUD.update(
            {"_id": ObjectId(post_id)}, {"$inc": {"reaction_count": 1}}
        )
        return {"status": "success", "message": "Reaction created successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def list_all_reaction_controller(post_id: str) -> Dict:
    try:
        reactions = await ReactionCRUD.read({"post_id": post_id})
        logger.info(f"Reactions: {reactions}")
        user_ids = [reaction.get("user_id") for reaction in reactions]
        user_infos = await gather(
            *[UserCRUD.find_by_id(user_id) for user_id in user_ids]
        )
        user_info_map = {
            user_info.get("_id"): user_info for user_info in user_infos if user_info
        }

        serialized_reactions = []
        for reaction in reactions:
            user_id = reaction.get("user_id")
            user_info = user_info_map.get(user_id)
            serialized_reaction = {
                "id": serialize_datetime(reaction.get("_id")),
                "user_id": reaction.get("user_id"),
                "post_id": reaction.get("post_id"),
                "type": reaction.get("type"),
                "created_at": serialize_datetime(reaction.get("created_at")),
                "updated_at": serialize_datetime(reaction.get("updated_at")),
                "user_info": (
                    {
                        "name": user_info.get("name"),
                        "picture": user_info.get("picture"),
                    }
                    if user_info
                    else None
                ),
            }
            serialized_reactions.append(serialized_reaction)
        return {"status": "success", "message": serialized_reactions}
    except Exception as e:
        logger.error(f"Error getting reaction: {str(e)}")
        return {"status": "error", "message": str(e)}


async def update_a_reaction_controller(
    user_id: str, reaction_id: str, type: int
) -> Dict:
    try:
        exist_data = await ReactionCRUD.find_by_id(reaction_id)
        if exist_data["user_id"] != user_id:
            return {
                "status": "error",
                "message": "You are not allowed to edit this reaction",
            }
        if exist_data is None:
            return {"status": "error", "message": "Reaction not found"}
        await ReactionCRUD.update(
            {"_id": ObjectId(reaction_id)},
            {
                "type": type,
            },
        )
        return {"status": "success", "message": "Reaction updated successfully"}
    except Exception as e:
        logger.error(f"Error updating reaction: {str(e)}")
        return {"status": "error", "message": str(e)}


async def delete_a_reaction_controller(user_id: str, reaction_id: str) -> Dict:
    try:
        exist_data = await ReactionCRUD.find_by_id(reaction_id)
        if exist_data["user_id"] != user_id:
            return {
                "status": "error",
                "message": "You are not allowed to delete this reaction",
            }
        if exist_data is None:
            return {"status": "error", "message": "Reaction not found"}
        await ReactionCRUD.delete({"_id": ObjectId(reaction_id)})
        await PostCRUD.update(
            {"_id": ObjectId(exist_data["post_id"])}, {"$inc": {"reaction_count": -1}}
        )
        return {"status": "success", "message": "Reaction deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting reaction: {str(e)}")
        return {"status": "error", "message": str(e)}
