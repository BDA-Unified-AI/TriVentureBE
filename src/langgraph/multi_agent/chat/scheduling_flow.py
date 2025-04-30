from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import tools_condition
from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage
from src.langgraph.tools.scheduling_tools import (
    create_a_activity,
    search_activities,
    update_a_activiy,
    delete_a_activity,
)
from src.langgraph.langchain.llm import llm
from src.langgraph.config.agent import Agent
from src.langgraph.utils_function.function_graph import (
    create_tool_node_with_fallback,
    human_review_node,
)
from src.langgraph.langchain.prompt import (
    scheduling_prompt,
    CompleteOrRoute,
    create_entry_node,
)
from src.langgraph.state import State
from src.utils.logger import logger
from src.langgraph.tools.plan_itinerary import plan_itinerary


class SchedulingAgent:
    def __init__(self, builder: StateGraph):
        self.builder = builder
        self.scheduling_safe_tools = [search_activities, plan_itinerary]
        self.scheduling_sensitive_tools = [
            create_a_activity,
            update_a_activiy,
            delete_a_activity,
        ]
        self.scheduling_tools = (
            self.scheduling_sensitive_tools + self.scheduling_safe_tools
        )
        self.scheduling_runnable = scheduling_prompt | llm.bind_tools(
            self.scheduling_tools + [CompleteOrRoute]
        )

    def route_scheduling(self, state: State):
        logger.info("Route scheduling")
        if (
            state["messages_history"] is not None
            and state["messages"][0].content == "y"
            and "Do you want to run the following tool(s)?"
            in state["messages_history"][-1].content
        ):
            if state["messages"][-1].tool_calls and state["messages"][-1].tool_calls[0][
                "name"
            ] in [r.name for r in self.scheduling_sensitive_tools]:
                logger.info("Sensitive tools")
                return "scheduling_sensitive_tools"
            logger.info("Safe tools")
            return END

        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        did_cancel = any(tc["name"] == CompleteOrRoute.__name__ for tc in tool_calls)
        logger.info(f"Did cancel: {did_cancel}")
        if did_cancel:
            return "leave_skill"
        tool_names = [t.name for t in self.scheduling_safe_tools]
        if all(tc["name"] in tool_names for tc in tool_calls):
            logger.info("Scheduling safe tools")
            return "scheduling_safe_tools"
        logger.info("User review")
        return "user_review_scheduling"

    def node(self):
        self.builder.add_node(
            "enter_schedule_activity",
            create_entry_node("Schedule Activity Assistant", "scheduling"),
        )
        self.builder.add_node("scheduling_agent", Agent(self.scheduling_runnable))
        self.builder.add_edge("enter_schedule_activity", "scheduling_agent")
        self.builder.add_node(
            "scheduling_safe_tools",
            create_tool_node_with_fallback(self.scheduling_safe_tools),
        )
        self.builder.add_node(
            "scheduling_sensitive_tools",
            create_tool_node_with_fallback(self.scheduling_sensitive_tools),
        )

        self.builder.add_node("user_review_scheduling", human_review_node)

    def edge(self):
        self.builder.add_edge("enter_schedule_activity", "scheduling_agent")

        self.builder.add_conditional_edges(
            "scheduling_agent",
            self.route_scheduling,
            {
                "scheduling_sensitive_tools": "scheduling_sensitive_tools",
                END: "save_history",
                "leave_skill": "leave_skill",
                "scheduling_safe_tools": "scheduling_safe_tools",
                "user_review_scheduling": "user_review_scheduling",
            },
        )

        self.builder.add_edge("user_review_scheduling", "save_history")
        self.builder.add_edge("scheduling_sensitive_tools", "scheduling_agent")
        self.builder.add_edge("scheduling_safe_tools", "scheduling_agent")

    def __call__(self):
        self.node()
        self.edge()
        return self.builder
