from langchain_core.messages import (
    BaseMessage,
    ToolMessage,
    AIMessage,
    HumanMessage,
    trim_messages,
)
from typing import Union
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableLambda
from src.langgraph.state import State
from src.utils.mongo import chat_messages_history
from src.utils.logger import logger


def fake_token_counter(messages: Union[list[BaseMessage], BaseMessage]) -> int:
    if isinstance(messages, list):
        return sum(len(message.content.split()) for message in messages)
    return len(messages.content.split())


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def handle_tool_error(state: State) -> dict:
    error = state.get("error")
    tool_messages = state["messages"][-1]
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_messages.tool_calls
        ]
    }


async def get_history(state: State, config):
    logger.info("Get history node")
    history = state["messages_history"] if state.get("messages_history") else None
    try:
        if history is None:
            session_id = config.get("configurable", {}).get("session_id")
            history = await chat_messages_history(session_id).aget_messages()
            # logger.info(f"Chat history: {history}")
            if not history:
                return {"messages_history": []}
        chat_message_history = trim_messages(
            history,
            strategy="last",
            token_counter=fake_token_counter,
            max_tokens=2000,
            start_on="human",
            end_on="ai",
            include_system=False,
            allow_partial=False,
        )
        # logger.info(f"Chat history: {chat_message_history}")
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        chat_message_history = []

    return {"messages_history": chat_message_history}


async def save_history(state: State, config):
    if not state["manual_save"]:
        return {"messages": []}
    message = state["messages"]
    user_input = message[0].content
    final_output = message[-1]
    session_id = config.get("configurable", {}).get("session_id")
    messages_add_to_history = [HumanMessage(user_input)]
    if isinstance(final_output, AIMessage):
        messages_add_to_history.append(AIMessage(final_output.content))
        history = chat_messages_history(session_id)
        await history.aadd_messages(messages_add_to_history)
    return {"messages": []}


def human_review_node(state: State):
    logger.info("Human review node")
    tool_calls = state["messages"][-1].tool_calls
    formatted_tool_calls = []
    user_message: HumanMessage = state["messages"][0]
    logger.info(f"User message: {user_message}")

    for call in tool_calls:
        args_str = "\n".join(
            f"#### {k.replace('_', ' ')}: {v}" for k, v in call["args"].items()
        )
        call_name_with_spaces = call["name"].replace("_", " ")
        formatted_call = f"""
**Tool calling**: {call_name_with_spaces}

**Arguments**:\n
{args_str}
"""
        formatted_tool_calls.append(formatted_call)

    format_message = (
        "#### Do you want to run the following tool(s)?\n\n"
        f"{chr(10).join(formatted_tool_calls)}\n\n"
        "Enter **'y'** to run or **'n'** to cancel:"
    )

    return {"messages": [AIMessage(format_message)], "accept": False}


def format_accommodation_markdown(data):
    formatted = ""
    for entry in data:
        formatted += f"### {entry['Accommodation Name']}\n"
        formatted += f"- **Address:** {entry['Address']}\n"
        formatted += f"- **Distance from center:** {entry['distance_km']}\n"

        contact_info = entry.get("contact")
        if contact_info:
            formatted += "- **Contact:**\n"
            if "phone" in contact_info:
                formatted += f"  - Phone: {contact_info['phone']}\n"
            if "email" in contact_info:
                formatted += f"  - Email: {contact_info['email']}\n"

        if "website" in entry:
            formatted += f"- **Website:** [{entry['website']}]({entry['website']})\n"

        accommodation_info = entry.get("accommodation")
        if accommodation_info:
            formatted += "- **Accommodation Info:**\n"
            if "stars" in accommodation_info:
                formatted += f"  - Stars: {accommodation_info['stars']}\n"
            if "rooms" in accommodation_info:
                formatted += f"  - Rooms: {accommodation_info['rooms']}\n"

        formatted += "\n---\n\n"

    return formatted
