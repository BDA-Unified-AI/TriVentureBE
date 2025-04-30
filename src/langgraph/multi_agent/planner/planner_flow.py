from dotenv import load_dotenv

load_dotenv()
from src.langgraph.langchain.llm import llm
from src.langgraph.tools.destination_tools import destination_suggestion
from src.langgraph.tools.search_tools import search_and_summarize_website
from .react_agent import create_react_agent
from src.langgraph.langchain.prompt import planner_prompt, parser_output_planner_prompt
from typing import TypedDict, Union, Any, Optional
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.exceptions import OutputParserException
from langgraph.graph import StateGraph, START, END
from src.utils.logger import logger
from src.utils.helper import format_include_destinations
import operator
from typing import Annotated
from .utils import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser


class State(TypedDict):
    llm_response: Annotated[list[Union[AgentAction, Any]], operator.add]
    tools_ouput: Annotated[list[str], operator.add]
    # error: Union[OutputParserException, Any]
    error: Optional[Any]
    duration: str
    start_date: str
    location: str
    interests: str
    nation: str
    include_destination: list
    limit_interation: int
    current_interation: int
    final_answer: str


parser = ReActSingleInputOutputParser()

tools = [destination_suggestion, search_and_summarize_website]
tools_mapping = {tool.name: tool for tool in tools}


async def agent_fn(state: State):
    llm_response = state["llm_response"]
    tools_output = state["tools_ouput"]
    error = state["error"]
    duration = state["duration"]
    start_date = state["start_date"]
    location = state["location"]
    interests = state["interests"]
    nation = state["nation"]
    include_destination = format_include_destinations(state["include_destination"])
    prompt = planner_prompt.partial(
        duration=duration,
        start_date=start_date,
        location=location,
        interests=interests,
        nation=nation,
        include_destination=include_destination,
    )
    if len(llm_response) != 0:
        agent_scratchpad = format_log_to_str(
            zip(llm_response, tools_output), llm_prefix=""
        )
    else:
        agent_scratchpad = ""
    if error:
        if isinstance(error, OutputParserException):
            error = error.observation
        agent_scratchpad += (
            "\nPrevious response have error: "
            + str(error)
            + "so agent will try to recover. Please return in right format defined in prompt"
        )
    agent = create_react_agent(llm, tools, prompt)
    try:
        response = await agent.ainvoke(agent_scratchpad)
        logger.info(f"-> Agent response {response.content}")
        response_paser: Union[AgentAction, AgentFinish] = parser.parse(response.content)
        return {
            "llm_response": [response_paser],
            "error": None,
        }
    except OutputParserException as e:
        response = e.observation
        logger.error(f"Error in agent invoke {e}")
        return {
            "error": e,
        }


def after_call_agent(state: State):
    error = state["error"]
    llm_response = state["llm_response"][-1]
    if isinstance(error, OutputParserException):
        logger.info("-> paser output 1")
        return "parse_output"
    else:
        logger.info("-> Tool")
        return "execute_tools"


async def excute_tools_fn(state: State):
    llm_response: AgentAction = state["llm_response"][-1]
    tool_call_name = llm_response.tool
    tool_args = llm_response.tool_input
    
    # Preprocess tool name to remove markdown formatting
    if tool_call_name.startswith("**") and tool_call_name.endswith("**"):
        tool_call_name = tool_call_name[2:-2]  # Remove ** from start and end
    elif tool_call_name.startswith("*") and tool_call_name.endswith("*"):
        tool_call_name = tool_call_name[1:-1]  # Remove * from start and end
    elif tool_call_name.startswith("`") and tool_call_name.endswith("`"):
        tool_call_name = tool_call_name[1:-1]  # Remove ` from start and end
    
    logger.info(f"-> Original tool name: {llm_response.tool}")
    logger.info(f"-> Processed tool name: {tool_call_name}")
    logger.info(f"-> Tool args: {tool_args}")
    
    if tool_call_name == "destination_suggestion":
        tool_response = await destination_suggestion.ainvoke(
            {"query": tool_args, "config": ""}
        )
    elif tool_call_name == "search_and_summarize_website":
        tool_response = await search_and_summarize_website.ainvoke({"query": tool_args})
    logger.info("-> Agent")
    return {
        "tools_ouput": [tool_response],
        "error": None,
        "current_interation": state["current_interation"] + 1,
    }


async def parser_output_fn(state: State):
    llm_response = state["llm_response"]
    tools_output = state["tools_ouput"]
    error = state["error"]
    duration = state["duration"]
    start_date = state["start_date"]
    location = state["location"]
    interests = state["interests"]
    nation = state["nation"]
    if len(llm_response) != 0:
        agent_scratchpad = format_log_to_str(
            zip(llm_response, tools_output), llm_prefix=""
        )
    else:
        agent_scratchpad = ""
    if error:
        if isinstance(error, OutputParserException):
            error = error.observation
        agent_scratchpad += (
            "\nPrevious response have error: "
            + str(error)
            + "so agent will try to recover. Please return in right format defined in prompt"
        )
    prompt = parser_output_planner_prompt.partial(
        duration=duration,
        start_date=start_date,
        location=location,
        interests=interests,
        nation=nation,
    )
    chain_output = prompt | llm
    output = await chain_output.ainvoke({"agent_scratchpad": agent_scratchpad})
    return {
        "final_answer": output.content,
    }


workflow = StateGraph(State)
workflow.add_node("agent", agent_fn)
workflow.add_node("execute_tools", excute_tools_fn)
workflow.add_node("parse_output", parser_output_fn)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    after_call_agent,
    {
        "parse_output": "parse_output",
        "execute_tools": "execute_tools",
    },
)


def after_execute_tools(state: State):
    if state["current_interation"] >= state["limit_interation"]:
        return "parse_output"
    return "agent"


workflow.add_conditional_edges(
    "execute_tools",
    after_execute_tools,
    {
        "parse_output": "parse_output",
        "agent": "agent",
    },
)
workflow.add_edge("parse_output", END)

planner_app = workflow.compile()
