from langchain.prompts import ChatPromptTemplate, PromptTemplate
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from typing import Callable
import pytz
from src.langgraph.state import State
from src.utils.logger import logger
from langchain_core.prompts import PromptTemplate
from .llm import llm, llm_flash
from src.langgraph.config.constant import available_categories

vietnam_timezone = pytz.timezone("Asia/Ho_Chi_Minh")
vietnam_time = datetime.now(vietnam_timezone).strftime("%Y-%m-%d %H:%M:%S")


def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    def create_entry(state: State):
        logger.info((f"Create entry node: {assistant_name}, {new_dialog_state}"))
        return {
            "entry_message": [
                HumanMessage(
                    content=f"""The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user.
                        The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name} and the booking, update, other other action is not complete until after you have successfully invoked the appropriate tool
                        If the user changes their mind or needs help for other tasks, call the CompleteOrRoute function to leave this assistant.
                        Do not mention who you are - just act as the proxy for the assistant.""",
                ),
            ],
        }

    return create_entry


primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful customer support assistant for TriVenture AI Corporation about traveling.
        Key guidelines:
        - Call tool destination_recommendation to recommend destinations when user want to go somewhere or ask for recommendation.
        - Using search engine to find an something relate to user's request.
        - Be persistent with searches and expand bounds if needed.
        - Answer in {language} language
        <<Current time: {current_time}>>,
        """,
        ),
        ("placeholder", "{history}"),
        ("placeholder", "{messages}"),
    ]
).partial(current_time=vietnam_time)

classify_user_intent_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
Your task is to classify the user's intent based on the message history.
Available intents are:
- book_hotel : if current user intent related to hotel booking, searching, or another information about hotel
- scheduling : if current user intent related to scheduling activities, planning, create calendar, timetable agent, plan itinerary
- other: if current user intent is not related to hotel booking or scheduling. It can be a general question, greeting, or other information(destination recommendation).

Output only user intent.
""",
        ),
        ("placeholder", "{history}"),
        ("placeholder", "{messages}"),
    ]
)

scheduling_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a part of agent in a multi agent system.
            You are a scheduling assistant for handling scheduling CRUD operations, plan itinerary(travel plan).
            Instructions:
                1. Using history to make content for conversation
                2. Call tool to create, update, delete, search activity when collect enough information.
                3. Not ask user for confirmation, automatically confirm call tool.
                4. start_time (str):  Ask the user for the start time of the activity. If not sure then return current time.
                5. end_time (str): Ask the user if they not mentioned the end time of the activity. If not sure then return the end time as 1 hour from the start time.
                6. start_time and end_time can be all day, morning, afternoon, evening, night, or specific time.
                7. Don't ask user more detail. You must naturally respond to the user's messages.

            Do not waste the user's time. Do not make up invalid tools or functions.
            Call CompleteOrRoute when user's intent is not related to scheduling. Another agent will take over.

            Some examples for which you must call CompleteOrRoute:
            - what's the weather like this time of year?
            - i need to figure out transportation while i'm there
            - Acitivity created successfully
            - I want recommend some travel destinations, hotels.
            Note:
            - Past conversation it can be response from another assistant. If your tool can't handle, you must call "CompleteOrRoute" to return to the host assistant.
            - Don't ask user confirmation the tool which you didn't bind.
            - Not required user typing in the format of tool call. You must naturally respond to the user's messages.
            - You must call "CompleteOrRoute" than say you can't handle the user's request.
            - Answer in {language} language
            <<Current time: {current_time}>> (Focus on current_time in the present moment, rather than the past conversation)
            """,
        ),
        ("placeholder", "{history}"),
        ("placeholder", "{entry_message}"),
        ("placeholder", "{messages}"),
    ]
).partial(current_time=vietnam_time)

book_hotel_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a part of agent in a multi agent system.
            Your goal is to assist the user asking for hotel recommendations and booking a hotel.
            Instructions:
            Your task:
                1. Using history to make content for conversation.
                2. Search for available hotels when the user asks for hotel recommendations.
                3. Execute then CRUD operations for booking a hotel base on user conversation.
                4. You must call "CompleteOrRoute" when last message is not related to hotel booking.
            
            Some examples for which you should CompleteOrRoute:
            - what's the weather like this time of year?
            - nevermind i think I'll book separately
            - I want create schedule, timetable, calendar
            - else not related to hotel booking
           
            Note: 
                - Past conversation it can be response from another assistant. If your tool can't handle, you must call "CompleteOrRoute" to return to the host assistant.
                - Don't ask user confirmation the tool which you didn't bind.
                - Not required user typing in the format of tool call. You must naturally respond to the user's messages.
                - Answer in {language} language

             <<Current time: {current_time}>>
            """,
        ),
        ("placeholder", "{history}"),
        ("placeholder", "{entry_message}"),
        ("placeholder", "{messages}"),
    ]
).partial(current_time=vietnam_time)

routing_recommender_prompt = PromptTemplate.from_template(
    """You are a tour guide.
### Instruction:
You are given a query sentence
Classify the query as 'characteristic', 'geographic' or 'invalid' based on its content.

- 'Characteristic' if it asks about a place's features (e.g., camping, relaxing, scenic).
- 'Geographic' if it involves location specifics (e.g., near a city, in a province, on a road).
- 'Invalid' if the query is not related to travel or destination.

###
Query sentence: {query}
"""
)
characteristic_extractor_prompt = PromptTemplate.from_template(
    """You are a tour guide.
### Instruction:
Read the sentence carefully
Given a query about a destination, extract two things:
1. **Kind**: Choose one from {available_categories}.
2. **Main Place**: Identify the main place mentioned in the query. Include 'Quy Nhon' or 'Binh Dinh' term in the main place response

Query sentence: {query}
."""
).partial(available_categories=list(available_categories.keys()))


class RoutingRecommender(BaseModel):
    label: str = Field(..., description="is 'characteristic', 'geographic' or 'invalid'")


class CharacteristicExtractor(BaseModel):
    kind: str = Field(
        ...,
        description=f"Choose one from {list(available_categories.keys())}",
    )
    main_place: str = Field(..., description="main place mentioned in the query")


routing_recommender_chain = (
    routing_recommender_prompt | llm_flash.with_structured_output(RoutingRecommender)
)

characteristic_extractor_chain = (
    characteristic_extractor_prompt
    | llm_flash.with_structured_output(CharacteristicExtractor)
)


class CompleteOrRoute(BaseModel):
    """Call this function to complete the current assistant's task and route the conversation back to the primary assistant. Must call this tool instead of saying you cannot handle the user's request."""

    reason: str


class HotelBookingAgent(BaseModel):
    """Transfer work to a specialized assistant to handle hotel bookings and search for available hotels."""


class ScheduleActivityAgent(BaseModel):
    """Transfer work to a schedule assistant to handle schedule activity calendar, schedule, timetable or planning."""


class ClassifyUserIntent(BaseModel):
    """Most relevant intent"""

    intent: str = Field(
        ...,
        description="User intent is classified into one of the following categories: book_hotel, scheduling, other",
    )


planner_prompt = PromptTemplate.from_template(
    """
Your are Amazing Travel Concierge!. Specialist in travel planning and logistics with decades of experience in the industry localted in {location}.
Your goal is create the most amazing Daily Itinerary: Plan a day-by-day schedule of what to do, including sightseeing, activities.
Create a detailed {duration}-day travel itinerary with the following specifications:

Start date: {start_date}
Location: {location}
Customer's interests: {interests}

Required components:
1. Travel destination recommendations.
2. Restaurant, street food suggestions for each meal (with cuisine type).

Required destinations must be included in the itinerary.
{include_destination}

Note: 
- Call tool destination_suggestion multiple times, with different queries to get a variety of recommendations.(query should be based on user interests).
- Call tool search_and_summarize_website(like search engine) to find information on websites.
- Using {nation} language for Final Answer.
- Using 24-hour time format for start_time and end_time (13:00 - 14:00) in format of (hour:minute).
- Use available tools to create a comprehensive travel plan.(If needed, you can call tool multiple times to get a variety of recommendations). 
- If have already enough information to build the itinerary, you need directly to Final Answer.

{tools}

Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Note: Always keep correct formatting and structure
**Begin!**


{agent_scratchpad}
"""
)


parser_output_planner_prompt = PromptTemplate.from_template(
    """Your task is build a travel itinerary for the user based on log of ReAct agent scratchpad. Specialist in travel planning and logistics with decades of experience in the industry localted in {location}.
Your goal is create the most amazing Daily Itinerary: Plan a day-by-day schedule of what to do, including sightseeing, activities.
Create a detailed {duration}-day travel itinerary with the following specifications:

Start date: {start_date}
Location: {location}
Customer's interests: {interests}

Required components for each day:
1. Travel destination recommendations.
2. Restaurant, street food suggestions for each meal (with cuisine type).

ReAct agent scratchpad: {agent_scratchpad}



Expect output format:

Format the of itinerary as a daily schedule with:

    Date (date with format month/day/year)
        (start_time - end_time): Activity 1 description
        (start_time - end_time): Activity 2 description
        ... (repeat for all activities scheduled for the day)
    Date (date with format month/day/year)
    ... (repeat for all days in the itinerary)

Note:
- Using {nation} language for description.
- Using 24-hour time format for start_time and end_time (13:00 - 14:00) in format of (hour:minute).
- Travel time is flexible from 7am to 10pm, time and location must be reasonable for morning, noon, afternoon and evening.
- Must include rest time in plan.
- Include all destinations, activities,... in only one messsage format structure described above.
- Not include beside information like transportation, local tips,...

""",
)
