from src.langgraph.config.constant import RedisCfg
import redis.asyncio as redis

# redis_client = redis.from_url(
#     RedisCfg.REDIS_URL, encoding="utf-8", decode_responses=True
# )


async def set_key_redis(key, value, time=300):
    return None #redis_client.set(key, value, time)


async def get_key_redis(key):
    
    return None #await redis_client.get(key)


async def delete_key_redis(key):
    return None#redis_client.delete(key)
