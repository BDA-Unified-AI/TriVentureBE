from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage, HumanMessage
from src.langgraph.state import State
from src.utils.logger import logger


class Agent:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    async def __call__(self, state: State):
        while True:
            messages = state["messages"]
            # message_logger = messages[-1].pretty_print()
            # logger.info(f"Message: {message_logger}")
            chat_history = state["messages_history"]
            if messages:
                messages = [
                    message
                    for message in messages
                    if not (
                        hasattr(message, "tool_calls")
                        and any(
                            tool_call["name"] == "CompleteOrRoute"
                            for tool_call in message.tool_calls
                        )
                    )
                ]
            intent = state["intent"]
            entry_message = state.get("entry_message")
            if (
                state["messages"][0].content == "y"
                and "Do you want to run the following tool(s)"
                in state["messages_history"][-1].content
                and isinstance(state["messages"][-1], HumanMessage)
            ):
                logger.info("AGENT CALL SENTITIVE TOOLS")
                data = {
                    "messages": [state["messages"][0]],
                    "history": [state["messages_history"][-1]],
                    "entry_message": entry_message,
                    "intent": intent,
                    "language": state["language"],
                }
                result = await self.runnable.ainvoke(data)
                # message_logger = result.pretty_print()
                # logger.info(f"Message: {message_logger}")
                try:
                    tool_name = result.tool_calls[0]["name"]
                    logger.info(f"Tool name: {tool_name}")
                    return {"messages": result, "tool_name": tool_name}
                except Exception as e:
                    logger.error(f"Error scheduling sensitive tools: {e}")
                    return {"messages": "Can't call tool"}

            if state["intent"] is None:
                messages = [
                    msg
                    for msg in messages
                    if not (
                        isinstance(msg, AIMessage)
                        and any(
                            tool_call["name"] == "CompleteOrRoute"
                            for tool_call in msg.tool_calls
                        )
                    )
                ]
            data = {
                "messages": messages,
                "history": chat_history,
                "entry_message": entry_message,
                "intent": intent,
                "language": state["language"],
            }
            result: AIMessage = await self.runnable.ainvoke(data)
            # message_logger = result.pretty_print()
            # logger.info(f"Message: {message_logger}")
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                logger.info("No content found, retrying")
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}
