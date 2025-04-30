from typing import Dict
from datetime import datetime
from src.utils.mongo import CommentCRUD, UserCRUD, PostCRUD
from src.utils.logger import logger
from datetime import datetime
from bson import ObjectId
from datetime import datetime
from bson import ObjectId
from asyncio import gather


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj


async def create_a_comment_controller(content: str, user_id: str, post_id: str) -> Dict:
    try:
        comment = {
            "content": content,
            "user_id": user_id,
            "post_id": post_id,
        }
        output = await CommentCRUD.create(comment)
        await PostCRUD.update(
            {"_id": ObjectId(post_id)}, {"$inc": {"comment_count": 1}}
        )
        return {"status": "success", "message": output}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_comments_of_a_post_controller(post_id: str) -> Dict:
    try:
        comments = await CommentCRUD.read({"post_id": post_id})
        logger.info(f"COMMENTS: {comments}")
        user_ids = [comment.get("user_id") for comment in comments]
        user_infos = await gather(
            *[UserCRUD.find_by_id(user_id) for user_id in user_ids]
        )
        user_info_map = {
            user_info.get("_id"): user_info for user_info in user_infos if user_info
        }

        serialized_comments = []
        for comment in comments:
            user_id = comment.get("user_id")
            user_info = user_info_map.get(user_id)
            serialized_comment = {
                "id": serialize_datetime(comment.get("_id")),
                "content": comment.get("content"),
                "user_id": comment.get("user_id"),
                "post_id": comment.get("post_id"),
                "created_at": serialize_datetime(comment.get("created_at")),
                "updated_at": serialize_datetime(comment.get("updated_at")),
                "user_info": (
                    {
                        "name": user_info.get("name"),
                        "picture": user_info.get("picture"),
                    }
                    if user_info
                    else None
                ),
            }
            serialized_comments.append(serialized_comment)
        return {"status": "success", "message": serialized_comments}
    except Exception as e:
        logger.error(f"Error getting post: {str(e)}")
        return {"status": "error", "message": str(e)}


async def update_a_comment_controller(
    user_id: str, comment_id: str, content: str
) -> Dict:
    try:
        exist_data = await CommentCRUD.find_by_id(comment_id)
        if exist_data is None:
            return {"status": "error", "message": "Comment not found"}
        if exist_data["user_id"] != user_id:
            return {
                "status": "error",
                "message": "You are not allowed to update this comment",
            }

        await CommentCRUD.update(
            {"_id": ObjectId(comment_id)},
            {
                "content": content,
            },
        )
        return {"status": "success", "message": "Post updated successfully"}
    except Exception as e:
        logger.error(f"Error updating post: {str(e)}")
        return {"status": "error", "message": str(e)}


async def delete_a_comment_controller(user_id: str, comment_id: str) -> Dict:
    try:
        exist_data = await CommentCRUD.find_by_id(comment_id)
        if exist_data is None:
            return {"status": "error", "message": "Comment not found"}
        if exist_data["user_id"] != user_id:
            return {
                "status": "error",
                "message": "You are not allowed to delete this comment",
            }

        await CommentCRUD.delete({"_id": ObjectId(comment_id)})
        await PostCRUD.update(
            {"_id": ObjectId(exist_data["post_id"])}, {"$inc": {"comment_count": -1}}
        )
        return {"status": "success", "message": "Comment deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting post: {str(e)}")
        return {"status": "error", "message": str(e)}
