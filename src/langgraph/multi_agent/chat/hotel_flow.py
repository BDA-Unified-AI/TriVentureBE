from langgraph.prebuilt import tools_condition
from langgraph.graph import END, StateGraph
from langchain_core.messages import ToolMessage, AIMessage
from src.langgraph.tools.hotel_tools import (
    book_hotel,
    update_hotel,
    cancel_hotel,
    search_hotels,
)
from src.langgraph.langchain.llm import llm
from src.langgraph.config.agent import Agent
from src.langgraph.utils_function.function_graph import (
    create_tool_node_with_fallback,
    human_review_node,
)
from src.langgraph.langchain.prompt import (
    book_hotel_prompt,
    CompleteOrRoute,
    create_entry_node,
)

from src.langgraph.state import State
from src.utils.logger import logger


def format_search_hotels_fn(state: State):
    for message in state["messages"]:
        if isinstance(message, ToolMessage) and message.name == "search_hotels":
            # new_content = f"Here are the search results for hotels near location which you can book:\n {message.content}"
            # return {"messages": AIMessage(content=new_content)}
            return {
                "messages": AIMessage(
                    content=message.content + "  on frontend for user to select"
                )
            }


class HotelBookingAgent:
    def __init__(self, builder: StateGraph):
        self.builder = builder
        self.book_hotel_safe_tools = [search_hotels]
        self.book_hotel_sensitive_tools = [book_hotel, update_hotel, cancel_hotel]
        self.book_hotel_tools = self.book_hotel_safe_tools
        self.book_hotel_runnable = book_hotel_prompt | llm.bind_tools(
            self.book_hotel_tools + [CompleteOrRoute]
        )

    @staticmethod
    def routing_user_review_book_hotel(state: State):
        if state["accept"] == True:
            return "book_hotel_sensitive_tools"
        return "save_history"

    @staticmethod
    def check_search_hotels(state: State):
        name = state["messages"][-1].name
        if name == "search_hotels":
            return "format_search_hotels"
        return "book_hotel_agent"

    def route_book_hotel(
        self,
        state: State,
    ):
        logger.info("Route book hotel")
        if (
            state["messages"][0].content == "y"
            and "Do you want to run the following tool(s)?"
            in state["messages_history"][-1].content
        ):
            if state["messages"][-1].tool_calls:
                return "book_hotel_sensitive_tools"
            return END
        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        did_cancel = any(tc["name"] == CompleteOrRoute.__name__ for tc in tool_calls)
        logger.info(f"Did cancel: {did_cancel}")
        if did_cancel:
            return "leave_skill"
        tool_names = [t.name for t in self.book_hotel_safe_tools]
        if all(tc["name"] in tool_names for tc in tool_calls):
            logger.info("Book hotel safe tools")
            return "book_hotel_safe_tools"
        logger.info("User review")
        return "user_review_book_hotel"

    def node(self):
        self.builder.add_node(
            "enter_book_hotel",
            create_entry_node("Hotel Booking Assistant", "book_hotel"),
        )
        self.builder.add_node("book_hotel_agent", Agent(self.book_hotel_runnable))
        self.builder.add_node(
            "book_hotel_safe_tools",
            create_tool_node_with_fallback(self.book_hotel_safe_tools),
        )
        self.builder.add_node(
            "book_hotel_sensitive_tools",
            create_tool_node_with_fallback(self.book_hotel_sensitive_tools),
        )
        self.builder.add_node("user_review_book_hotel", human_review_node)
        self.builder.add_node("format_search_hotels", format_search_hotels_fn)

    def edge(self):
        self.builder.add_edge("enter_book_hotel", "book_hotel_agent")
        self.builder.add_conditional_edges(
            "user_review_book_hotel",
            self.routing_user_review_book_hotel,
            {
                "book_hotel_sensitive_tools": "book_hotel_sensitive_tools",
                "save_history": "save_history",
            },
        )
        self.builder.add_edge("book_hotel_sensitive_tools", "book_hotel_agent")
        self.builder.add_conditional_edges(
            "book_hotel_safe_tools",
            self.check_search_hotels,
            {
                "book_hotel_agent": "book_hotel_agent",
                "format_search_hotels": "format_search_hotels",
            },
        )
        self.builder.add_edge("format_search_hotels", "save_history")
        self.builder.add_conditional_edges(
            "book_hotel_agent",
            self.route_book_hotel,
            {
                "book_hotel_sensitive_tools": "book_hotel_sensitive_tools",
                END: "save_history",
                "leave_skill": "leave_skill",
                "book_hotel_safe_tools": "book_hotel_safe_tools",
                "user_review_book_hotel": "user_review_book_hotel",
            },
        )

    def __call__(self):
        self.node()
        self.edge()
        return self.builder
