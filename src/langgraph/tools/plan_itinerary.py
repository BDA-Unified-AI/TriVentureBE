from langchain_core.tools import tool

from langchain_core.runnables.config import RunnableConfig
from typing import Optional
from src.langgraph.multi_agent.planner.planner_flow import planner_app


@tool
async def plan_itinerary(
    duration: int,
    interests: str,
    include_destination: Optional[str],
    config: RunnableConfig,
):
    """Call to planner to make a travel itinerary for a period of time in Quy Nhon, Vietnam.

    Args:
    duration (int): number of travel
    interests (str): interests of the travel(natural, culture, etc.)
    include_destination (Optional[str]): include destination in the itinerary
    """
    # input_graph = {
    #     "duration": duration,
    #     "start_date": start_date,
    #     "location": "Quy Nhon",
    #     "interests": interests,
    #     "nation": "Vietnam",
    #     "include_destination": include_destination,
    #     "limit_interation": 10,
    #     "current_interation": 0,
    #     "error": None,
    # }
    # output = await planner_app.ainvoke(input_graph, config)
    # Use path parameters for cleaner URLs that won't break in chat interfaces
    # Remove spaces from parameters to ensure URL works correctly
    clean_interests = interests.replace(" ", "") if interests else ","
    clean_location = "QuyNhon,Vietnam"  # Removing spaces in location
    clean_destination = include_destination.replace(" ", "") if include_destination else ","

    url = f"https://triventure.vercel.app/planner/{duration}/{clean_interests}/{clean_location}/{clean_destination}"
    return "Markdown string: " + f"[Vào đây để tạo kế hoạch]({url})"
