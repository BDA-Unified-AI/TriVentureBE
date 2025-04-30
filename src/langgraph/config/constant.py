import os
class StateCfg:
    MESSAGES = "messages"
    INTENT = "intent"
    HISTORY = "messages_history"
    USER_FEEDBACK = "user_feedback"


class MongoCfg:
    MONGODB_URL: str = os.getenv("MONGODB_URL")
    MONGO_INDEX: str = os.getenv("MONGO_INDEX")
    USER: str = "user"
    ACTIVITY: str = "activity"
    DATE: str = "date"
    BOOK_HOTEL: str = "book_hotel"
    CHAT_HISTORY: str = "chat_history"
    POST: str = "post"
    COMMENT: str = "comment"
    REACTION: str = "reaction"
    DESTINATION: str = "destination"
    MAX_HISTORY_SIZE: int = 15
class RedisCfg:
    REDIS_URL: str = os.getenv("REDIS_URL")

available_categories = {
    "food_and_beverage": "catering",
    "accommodation": "accommodation",
    "entertainment": "entertainment",
    "leisure": "leisure",
    "natural": "natural",
    "national_park": "national_park",
    "tourism": "tourism",
    "camping": "camping",
    "religion": "religion",
    "sport": "sport",
    "commercial": "commercial",
}