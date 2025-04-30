from langgraph.graph import END, START, StateGraph
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import tools_condition
from src.langgraph.langchain.llm import llm
from src.langgraph.config.agent import Agent
from src.langgraph.state import State
from src.langgraph.langchain.prompt import (
    primary_assistant_prompt,
    classify_user_intent_prompt,
    ClassifyUserIntent,
    HotelBookingAgent,
    ScheduleActivityAgent,
)
from src.langgraph.utils_function.function_graph import (
    create_tool_node_with_fallback,
    get_history,
    save_history,
)
from src.langgraph.tools.destination_tools import destination_suggestion, get_weather
from src.utils.logger import logger

primary_assistant_tools = [
    TavilySearchResults(max_results=2),
    destination_suggestion,
    get_weather,
]

assistant_runnable = primary_assistant_prompt | llm.bind_tools(
    primary_assistant_tools + [ScheduleActivityAgent, HotelBookingAgent]
)


def leave_skill_fn(state: State):
    return {"intent": None, "ever_leave_skill": True}


from src.langgraph.multi_agent.chat.scheduling_flow import SchedulingAgent
from src.langgraph.multi_agent.chat.hotel_flow import HotelBookingAgent


async def classify_user_intent_fn(state: State):
    if state["intent"] is not None:
        return {"intent": state["intent"]}
    elif not state["intent"] and state["ever_leave_skill"]:
        return {"intent": None}
    user_query = state["messages"]
    history = state["messages_history"]
    chain_classify = classify_user_intent_prompt | llm.with_structured_output(
        ClassifyUserIntent
    )
    response: ClassifyUserIntent = await chain_classify.ainvoke(
        {"messages": [user_query[0]], "history": history}
    )
    logger.info(f"Classify user intent: {response.intent}")
    return {"intent": None if response.intent == "other" else response.intent}


class ChatBot:
    def __init__(self):
        self.builder = StateGraph(State)
        self.primary_assistant_tools = [
            TavilySearchResults(max_results=2),
            destination_suggestion,
            get_weather,
        ]
        self.assistant_runnable = assistant_runnable

    @staticmethod
    def routing_assistant(state: State):
        logger.info("Routing assistant")
        if state["intent"] is None:
            logger.info("No intent")
            return "primary_assistant"
        elif state["intent"] == "book_hotel":
            logger.info("Book hotel")
            return "enter_book_hotel"
        elif state["intent"] == "scheduling":
            logger.info("Scheduling")
            return "enter_schedule_activity"

    @staticmethod
    def route_primary_assistant(
        state: State,
    ):
        logger.info("Route primary assistant")
        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        if tool_calls:
            if tool_calls[0]["name"] == HotelBookingAgent.__name__:
                logger.info("To hotel booking assistant")
                return "enter_book_hotel"
            if tool_calls[0]["name"] == ScheduleActivityAgent.__name__:
                logger.info("To schedule activity")
                return "enter_schedule_activity"
            logger.info("Not hotel booking assistant")
            return "primary_assistant_tools"
        raise ValueError("Invalid route")

    def node(self):
        self.builder.add_node("leave_skill", leave_skill_fn)
        self.builder.add_node("fetch_history", get_history)
        self.builder.add_node("classify_intent", classify_user_intent_fn)
        self.builder.add_node("primary_assistant", Agent(self.assistant_runnable))
        self.builder.add_node(
            "primary_assistant_tools",
            create_tool_node_with_fallback(self.primary_assistant_tools),
        )
        self.builder.add_node("save_history", save_history)

    def edge(self):
        self.builder.add_edge(START, "fetch_history")
        self.builder.add_edge("fetch_history", "classify_intent")
        self.builder.add_conditional_edges(
            "classify_intent",
            self.routing_assistant,
            {
                "primary_assistant": "primary_assistant",
                "enter_book_hotel": "enter_book_hotel",
                "enter_schedule_activity": "enter_schedule_activity",
            },
        )
        self.builder.add_conditional_edges(
            "primary_assistant",
            self.route_primary_assistant,
            {
                END: "save_history",
                "enter_book_hotel": "enter_book_hotel",
                "enter_schedule_activity": "enter_schedule_activity",
                "primary_assistant_tools": "primary_assistant_tools",
            },
        )

        self.builder.add_edge("leave_skill", "classify_intent")
        self.builder.add_edge("primary_assistant_tools", "primary_assistant")
        self.builder.add_edge("save_history", END)

    def agent_connection(self):
        schedule = HotelBookingAgent(self.builder)
        hotel = SchedulingAgent(self.builder)
        self.builder = schedule()
        self.builder = hotel()

    def __call__(self):
        self.node()
        self.edge()
        self.agent_connection()
        return self.builder.compile()
