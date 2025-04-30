from typing_extensions import TypedDict, Annotated, Sequence
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.messages import BaseMessage


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    intent: str
    messages_history: list[AnyMessage]
    manual_save: bool
    accept: bool
    entry_message: BaseMessage
    tool_name: str
    language: str
    ever_leave_skill: bool
