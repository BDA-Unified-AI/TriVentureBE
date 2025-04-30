from typing import Dict
from src.utils.mongo import PostCRUD
from src.utils.logger import logger
from src.utils.mongo import UserCRUD, ReactionCRUD, DestinationCRUD
from asyncio import gather
from src.utils.helper import call_external_api, serialize_datetime
from datetime import datetime
from bson import ObjectId
import math


async def create_a_post_controller(
    content: str, user_id: str, destination_id: str, images: list
) -> Dict:
    try:
        image_url = await call_external_api(
            method="POST",
            # url="http://localhost:8000/upload_image",
            # url="https://abao77-image-retrieval.hf.space/upload_image",
            url="https://abao77-image-retrieval-full.hf.space/upload_image",
            json={"base64_image": images},
        )
        print(f"IMAGE URL: {image_url}")
        post = {
            "content": content,
            "user_id": user_id,
            "destination_id": destination_id,
            "comment_count": 0,
            "reaction_count": 0,
            "picture": image_url["public_url"] if image_url.get("public_url") else None,
            "like": [],
        }
        await PostCRUD.create(post)
        return {"status": "success", "message": "Post created successfully"}
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        return {"status": "error", "message": str(e)}


async def get_a_post_controller(post_id: str) -> Dict:
    try:
        post = await PostCRUD.find_by_id(post_id)
        if post is None:
            return {"status": "error", "message": "Post not found"}

        serialized_post = {
            "id": serialize_datetime(post.get("_id")),
            "content": post.get("content"),
            "user_id": post.get("user_id"),
            "destination_id": post.get("destination_id"),
            "comment_count": post.get("comment_count", 0),
            "reaction_count": post.get("reaction_count", 0),
            "created_at": serialize_datetime(post.get("created_at")),
            "updated_at": serialize_datetime(post.get("updated_at")),
        }

        return {"status": "success", "message": serialized_post}
    except Exception as e:
        logger.error(f"Error getting post: {str(e)}")
        return {"status": "error", "message": str(e)}


async def list_all_posts_controller(user_id: str, page: int = 1):
    try:
        PAGE_SIZE = 5
        # Calculate skip value for pagination
        skip = (page - 1) * PAGE_SIZE

        # Get total count for pagination metadata
        total_items = await PostCRUD.count({})
        total_pages = math.ceil(total_items / PAGE_SIZE)

        # Get paginated posts
        posts = await PostCRUD.find_many(
            filter={},  # Empty filter means get all
            skip=skip,
            limit=PAGE_SIZE,
            sort=[("created_at", -1)],  # Sort by created_at descending
        )

        user_ids = list({post.get("user_id") for post in posts})
        user_infos = await gather(*[UserCRUD.find_by_id(uid) for uid in user_ids])
        user_info_map = {
            info.get("_id"): {
                "user_id": info.get("_id"),
                "name": info.get("name"),
                "picture": info.get("picture"),
            }
            for info in user_infos
            if info
        }
        destination_ids = list({post.get("destination_id") for post in posts})
        destination_infos = await gather(
            *[DestinationCRUD.find_by_id(did) for did in destination_ids]
        )
        destination_info_map = {
            info.get("_id"): info.get("name") for info in destination_infos if info
        }
        formatted_user_reactions_map = {}
        if user_id:
            all_post_ids = [serialize_datetime(post.get("_id")) for post in posts]
            reactions = await gather(
                *[
                    ReactionCRUD.read_one({"user_id": user_id, "post_id": post_id})
                    for post_id in all_post_ids
                ]
            )
            for reaction in reactions:
                if reaction:
                    post_id = reaction.get("post_id")
                    formatted_user_reactions_map[post_id] = {
                        "id": serialize_datetime(reaction.get("_id")),
                        "post_id": post_id,
                        "user_id": reaction.get("user_id"),
                        "reaction_type": reaction.get("type"),
                    }
        serialized_posts = []
        for post in posts:
            post_id = serialize_datetime(post.get("_id"))
            uid = post.get("user_id")
            dest_id = post.get("destination_id")
            serialized_post = {
                "id": post_id,
                "content": post.get("content"),
                "destination_id": dest_id,
                "destination_name": destination_info_map.get(dest_id),
                "comment_count": post.get("comment_count", []),
                "reaction_count": post.get("reaction_count", []),
                "current_user_reaction": formatted_user_reactions_map.get(post_id),
                "picture": post.get("picture", []),
                "created_at": serialize_datetime(post.get("created_at")),
                "updated_at": serialize_datetime(post.get("updated_at")),
                "user_info": user_info_map.get(uid),
            }
            serialized_posts.append(serialized_post)

        return {
            "status": "success",
            "message": {
                "data": serialized_posts,
                "page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "page_size": PAGE_SIZE,
            },
        }

    except Exception as e:
        logger.error(f"Error listing posts: {str(e)}")
        return {"status": "error", "message": str(e)}


async def list_posts_by_destination_controller(
    destination_id: str, user_id: str, page: int = 1
):
    try:
        PAGE_SIZE = 5  # Changed from 1 to 5 posts per page
        # Calculate skip value for pagination
        skip = (page - 1) * PAGE_SIZE

        # Get total count for pagination metadata
        total_items = await PostCRUD.count({"destination_id": destination_id})
        total_pages = math.ceil(total_items / PAGE_SIZE)

        # Get paginated posts
        posts = await PostCRUD.find_many(
            filter={"destination_id": destination_id},
            skip=skip,
            limit=PAGE_SIZE,
            sort=[("created_at", -1)],  # Sort by created_at descending
        )

        if not posts:
            return {
                "status": "success",
                "message": {
                    "data": [],
                    "page": page,
                    "total_pages": total_pages,
                    "total_items": total_items,
                    "page_size": PAGE_SIZE,
                },
            }

        # Get unique user_ids
        user_ids = list({post.get("user_id") for post in posts})
        user_infos = await gather(*[UserCRUD.find_by_id(uid) for uid in user_ids])
        user_info_map = {
            info.get("_id"): {
                "user_id": info.get("_id"),
                "name": info.get("name"),
                "picture": info.get("picture"),
            }
            for info in user_infos
            if info
        }

        # Get destination name
        destination_info = await DestinationCRUD.find_by_id(destination_id)
        destination_name = destination_info.get("name") if destination_info else None

        # Reactions by current user for these posts
        formatted_user_reactions_map = {}
        if user_id:
            all_post_ids = [serialize_datetime(post.get("_id")) for post in posts]
            reactions = await gather(
                *[
                    ReactionCRUD.read_one({"user_id": user_id, "post_id": post_id})
                    for post_id in all_post_ids
                ]
            )
            for reaction in reactions:
                if reaction:
                    post_id = reaction.get("post_id")
                    formatted_user_reactions_map[post_id] = {
                        "id": serialize_datetime(reaction.get("_id")),
                        "post_id": post_id,
                        "user_id": reaction.get("user_id"),
                        "reaction_type": reaction.get("type"),
                    }

        # Final serialization
        serialized_posts = []
        for post in posts:
            post_id = serialize_datetime(post.get("_id"))
            uid = post.get("user_id")
            serialized_post = {
                "id": post_id,
                "content": post.get("content"),
                "destination_id": destination_id,
                "destination_name": destination_name,
                "comment_count": post.get("comment_count", []),
                "reaction_count": post.get("reaction_count", []),
                "current_user_reaction": formatted_user_reactions_map.get(post_id),
                "picture": post.get("picture", []),
                "created_at": serialize_datetime(post.get("created_at")),
                "updated_at": serialize_datetime(post.get("updated_at")),
                "user_info": user_info_map.get(uid),
            }
            serialized_posts.append(serialized_post)

        return {
            "status": "success",
            "message": {
                "data": serialized_posts,
                "page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "page_size": PAGE_SIZE,
            },
        }

    except Exception as e:
        logger.error(f"Error listing posts by destination: {str(e)}")
        return {"status": "error", "message": str(e)}


async def update_a_post_controller(user_id: str, post_id: str, content: str) -> Dict:
    try:
        exist_data = await PostCRUD.find_by_id(post_id)
        if exist_data["user_id"] != user_id:
            return {
                "status": "error",
                "message": "You are not allowed to update this post",
            }
        if exist_data is None:
            return {"status": "error", "message": "Post not found"}
        await PostCRUD.update(
            {"_id": ObjectId(post_id)},
            {
                "content": content,
            },
        )
        return {"status": "success", "message": "Post updated successfully"}
    except Exception as e:
        logger.error(f"Error updating post: {str(e)}")
        return {"status": "error", "message": str(e)}


async def delete_a_post_controller(user_id: str, post_id: str) -> Dict:
    try:
        exist_data = await PostCRUD.find_by_id(post_id)
        if exist_data["user_id"] != user_id:
            return {
                "status": "error",
                "message": "You are not allowed to delete this post",
            }
        if exist_data is None:
            return {"status": "error", "message": "Post not found"}
        await PostCRUD.delete({"_id": ObjectId(post_id)})
        return {"status": "success", "message": "Post deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting post: {str(e)}")
        return {"status": "error", "message": str(e)}
