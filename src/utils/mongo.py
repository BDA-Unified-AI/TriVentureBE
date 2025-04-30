from src.langgraph.config.constant import MongoCfg, RedisCfg
from src.utils.logger import logger
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_redis import RedisChatMessageHistory
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Type, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from datetime import datetime, timezone, timedelta
from src.apis.models.post_models import Comment, Reaction, Post
from src.apis.models.destination_models import Destination
from src.apis.models.schedule_models import Schedule
from src.apis.models.hotel_models import BookHotel
from src.apis.interfaces.api_interface import ChatHistoryManagement
from src.apis.models.user_models import User
from src.utils.logger import get_date_time

client: AsyncIOMotorClient = AsyncIOMotorClient(MongoCfg.MONGODB_URL)
database = client[MongoCfg.MONGO_INDEX]


class MongoCRUD:
    def __init__(
        self,
        collection: AsyncIOMotorCollection,
        model: Type[BaseModel],
        ttl_seconds: Optional[int] = None,
    ):
        self.collection = collection
        self.model = model
        self.ttl_seconds = ttl_seconds
        self._index_created = False

    async def _ensure_ttl_index(self):
        """Ensure TTL index exists"""
        if self.ttl_seconds is not None and not self._index_created:
            await self.collection.create_index("expire_at", expireAfterSeconds=0)
            self._index_created = True

    def _order_fields(self, doc: Dict) -> Dict:
        """Order fields in the document to ensure created_at and updated_at are at the end."""
        ordered_doc = {
            k: doc[k] for k in doc if k not in ["created_at", "updated_at", "expire_at"]
        }
        if "id" in doc:
            ordered_doc["_id"] = ObjectId(doc["id"])
        if "created_at" in doc:
            ordered_doc["created_at"] = doc["created_at"]
        if "updated_at" in doc:
            ordered_doc["updated_at"] = doc["updated_at"]
        if "expire_at" in doc:
            ordered_doc["expire_at"] = doc["expire_at"]
        return ordered_doc

    async def create(self, data: Dict) -> str:
        """Create a new document in the collection asynchronously, optionally using a user-specified ID."""
        await self._ensure_ttl_index()
        now = get_date_time().replace(tzinfo=None)
        data["created_at"] = now
        data["updated_at"] = now
        if self.ttl_seconds is not None:
            data["expire_at"] = now + timedelta(seconds=self.ttl_seconds)
        document = self.model(**data).model_dump(exclude_unset=True)
        ordered_document = self._order_fields(document)
        result = await self.collection.insert_one(ordered_document)
        return str(result.inserted_id)

    async def read(self, query: Dict) -> List[Dict]:
        """Read documents from the collection based on a query asynchronously."""
        cursor = self.collection.find(query)
        docs = []
        async for doc in cursor:
            docs.append(
                {
                    "_id": str(doc["_id"]),
                    **self._order_fields(self.model(**doc).model_dump(exclude={"id"})),
                }
            )
        return docs

    async def read_one(self, query: Dict) -> Optional[Dict]:
        """Read a single document from the collection based on a query asynchronously."""
        doc = await self.collection.find_one(query)
        if doc:
            doc["_id"] = str(doc["_id"])
            return {
                "_id": doc["_id"],
                **self._order_fields(self.model(**doc).model_dump(exclude={"id"})),
            }
        return None

    async def update(self, query: Dict, data: Dict) -> int:
        """Update documents in the collection based on a query asynchronously."""
        await self._ensure_ttl_index()

        # Check if update operators like $inc, $set, etc., are used
        if any(key.startswith("$") for key in data.keys()):
            update_data = data
        else:
            # If no MongoDB operators are used, treat it as a normal update
            data["updated_at"] = get_date_time().replace(tzinfo=None)
            if self.ttl_seconds is not None:
                data["expire_at"] = data["updated_at"] + timedelta(
                    seconds=self.ttl_seconds
                )
            update_data = {
                "$set": self._order_fields(
                    self.model(**data).model_dump(exclude_unset=True)
                )
            }

        result = await self.collection.update_many(query, update_data)
        return result.modified_count

    async def delete(self, query: Dict) -> int:
        """Delete documents from the collection based on a query asynchronously."""
        result = await self.collection.delete_many(query)
        return result.deleted_count

    async def delete_one(self, query: Dict) -> int:
        """Delete a single document from the collection based on a query asynchronously."""
        result = await self.collection.delete_one(query)
        return result.deleted_count

    async def find_by_id(self, id: str) -> Optional[Dict]:
        """Find a document by its ID asynchronously."""
        return await self.read_one({"_id": ObjectId(id)})

    async def find_all(self) -> List[Dict]:
        """Find all documents in the collection asynchronously."""
        return await self.read({})

    async def find_many(
        self, filter: Dict, skip: int = 0, limit: int = 0, sort: List[tuple] = None
    ) -> List[Dict]:
        """
        Find documents based on filter with pagination support.

        Args:
            filter: MongoDB query filter
            skip: Number of documents to skip
            limit: Maximum number of documents to return (0 means no limit)
            sort: Optional sorting parameters [(field_name, direction)]
                  where direction is 1 for ascending, -1 for descending

        Returns:
            List of documents matching the filter
        """
        cursor = self.collection.find(filter)

        # Apply pagination
        if skip > 0:
            cursor = cursor.skip(skip)
        if limit > 0:
            cursor = cursor.limit(limit)

        # Apply sorting if provided
        if sort:
            cursor = cursor.sort(sort)

        docs = []
        async for doc in cursor:
            # Convert _id to string and prepare document
            doc_id = str(doc["_id"])
            doc_copy = {**doc}
            doc_copy["_id"] = doc_id

            # Process through model validation
            try:
                validated_doc = self.model(**doc_copy).model_dump(exclude={"id"})
                docs.append({"_id": doc_id, **self._order_fields(validated_doc)})
            except Exception as e:
                logger.error(f"Error validating document {doc_id}: {str(e)}")
                # Include document even if validation fails, but with original data
                docs.append(
                    {"_id": doc_id, **{k: v for k, v in doc.items() if k != "_id"}}
                )

        return docs

    async def count(self, filter: Dict) -> int:
        """
        Count documents matching the filter.

        Args:
            filter: MongoDB query filter

        Returns:
            Number of documents matching the filter
        """
        try:
            return await self.collection.count_documents(filter)
        except Exception as e:
            logger.error(f"Error counting documents: {str(e)}")
            return 0


def chat_messages_history(
    session_id: str, number_of_messages: int = MongoCfg.MAX_HISTORY_SIZE, db="mongo"
):
    if not session_id:
        session_id = "12345678910"
        logger.warning("Session ID not provided, using default session ID")
    if db == "redis":
        return RedisChatMessageHistory(
            session_id=session_id,
            redis_url=RedisCfg.REDIS_URL,
            # ttl=605000,
            ttl=40000,
        )
    return MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string=MongoCfg.MONGODB_URL,
        database_name=MongoCfg.MONGO_INDEX,
        collection_name=MongoCfg.CHAT_HISTORY,
        history_size=number_of_messages,
    )


BookHotelCRUD = MongoCRUD(database[MongoCfg.BOOK_HOTEL], BookHotel)
ScheduleCRUD = MongoCRUD(database[MongoCfg.ACTIVITY], Schedule)
UserCRUD = MongoCRUD(database[MongoCfg.USER], User)
PostCRUD = MongoCRUD(database[MongoCfg.POST], Post)
ReactionCRUD = MongoCRUD(database[MongoCfg.REACTION], Reaction)
CommentCRUD = MongoCRUD(database[MongoCfg.COMMENT], Comment)
DestinationCRUD = MongoCRUD(database[MongoCfg.DESTINATION], Destination)

chat_history_management_crud = MongoCRUD(
    database["chat_history_management"], ChatHistoryManagement, 3600
)
