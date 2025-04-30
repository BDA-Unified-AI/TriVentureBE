from typing import List, Dict, Any
import aiohttp
from fastapi import HTTPException
from src.utils.logger import logger
import json
from src.langgraph.langchain.prompt import (
    routing_recommender_chain,
    characteristic_extractor_chain,
    RoutingRecommender,
    CharacteristicExtractor,
)
from src.apis.controllers.location_controller import (
    get_lat_long_location,
    get_places,
)
from src.langgraph.config.constant import available_categories
from src.utils.logger import logger


async def destination_suggestion_controller(
    question: str, user_id: str, top_k: int = 5
) -> List[Dict[str, Any]]:
    url = f"https://abao77-destination-suggestion.hf.space/model/get_destinations_list_by_question/{question}/{top_k}"
    if user_id:
        url += f"/{user_id}"
        logger.info("Call recommend with user_id")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Destination suggestion for question: {data}")
                    return data["destinations_list"]
                else:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Destinations request failed with status {response.status}",
                    )

        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


async def destination_recommendation_func(
    query, user_id: str, top_k=5, tool_chat=False
):
    routing: RoutingRecommender = await routing_recommender_chain.ainvoke(
        {"query": query}
    )
    print("routing", routing)
    if routing.label == "invalid":
        if tool_chat:
            return "the input message is not related to travel or destination"
        raise HTTPException(
            status_code=400,
            detail="The input is not related to travel or destination recommendations. Please provide a travel-related query.",
        )
    elif routing.label == "characteristic":
        output = await destination_suggestion_controller(query, user_id, top_k)
        if tool_chat:
            return output
        output = [
            {
                "name": i,
                "map_url": "https://www.google.com/maps/search/109.23333,13.76667",
            }
            for i in output
        ]
        return output
    characteristic_extract_response: CharacteristicExtractor = (
        await characteristic_extractor_chain.ainvoke({"query": query})
    )
    lat, lon = get_lat_long_location(characteristic_extract_response.main_place)
    response = get_places(
        lat,
        lon,
        5000,
        available_categories.get(characteristic_extract_response.kind, None),
        top_k,
    )
    output = json.loads(response.body)
    if tool_chat:
        output = [
            {
                "name": i["name"],
                "address": i["address"],
                "distance_km": i["distance_km"],
            }
            for i in output
        ]

    return output
