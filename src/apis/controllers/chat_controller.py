from langchain_core.messages import HumanMessage, AIMessage
from src.utils.mongo import chat_messages_history
from src.utils.logger import logger
from src.utils.mongo import chat_history_management_crud
from src.apis.interfaces.api_interface import Chat
from src.utils.helper import handle_validator_raise
from src.utils.redis import get_key_redis, set_key_redis
import json
from langchain_core.messages.ai import AIMessageChunk
from fastapi import BackgroundTasks
from fastapi.responses import JSONResponse
from src.langgraph.multi_agent.chat.chat_flow import ChatBot

app = ChatBot()
workflow = app()


@handle_validator_raise
def post_process_history(history):
    processed_history = []
    for entry in history:
        if entry["type"] == "human":
            processed_history.append(HumanMessage(content=entry["content"]))
        elif entry["type"] == "ai":
            processed_history.append(AIMessage(content=entry["content"]))
    return processed_history


async def save_history(user_id, human_message, ai_message, intent):
    messages_add_to_history = [HumanMessage(human_message), AIMessage(ai_message)]
    messages_add_to_history_dict = [
        {"type": "human", "content": human_message},
        {"type": "ai", "content": ai_message},
    ]
    messages_add_to_history_cache = {
        "message": messages_add_to_history_dict,
        "intent": intent,
    }
    history = chat_messages_history(user_id)
    await history.aadd_messages(messages_add_to_history)
    check_exist_history = await chat_history_management_crud.read_one(
        {"session_id": user_id}
    )
    if check_exist_history is None:
        await chat_history_management_crud.create(
            {"user_id": user_id, "session_id": user_id, "intent": intent}
        )
        logger.info("History created")
    else:
        await chat_history_management_crud.update(
            {"session_id": user_id}, {"intent": intent}
        )
        logger.info("History updated")
    history_cache = await get_key_redis(f"chat_history_{user_id}")
    if history_cache is not None:
        history_cache = eval(history_cache)
        history_cache["message"] = (
            history_cache["message"] + messages_add_to_history_dict
        )
        history_cache["intent"] = intent
        await set_key_redis(
            f"chat_history_{user_id}",
            str(history_cache),
        )
        return {"message": "History updated"}
    await set_key_redis(f"chat_history_{user_id}", str(messages_add_to_history_cache))
    return {"message": "History created"}


async def chat_streaming_function(user, data: Chat, background_tasks: BackgroundTasks):
    try:
        human_message = data.message
        history = data.history
        lat = data.lat
        long = data.long
        language = data.language
        logger.info(f"Language: {language}")

        try:
            process_history = post_process_history(history) if history is not None else None
        except Exception as e:
            logger.error(f"Error processing chat history: {str(e)}")
            yield json.dumps({"type": "error", "content": "Error processing chat history" + str(e)}, ensure_ascii=False) + "\n"
            return

        config = {
            "configurable": {
                "user_id": user["id"],
                "user_email": user["email"],
                "contact_number": user["contact_number"],
                "session_id": user["id"],
                "lat": lat,
                "long": long,
            }
        }

        initial_input = {
            "messages": [("user", human_message)],
            "messages_history": process_history,
            "entry_message": None,
            "manual_save": False,
            "intent": data.intent,
            "language": language,
            "tool_name": None,
            "ever_leave_skill": False,
        }

        last_output_state = None
        temp = ""

        try:
            async for event in workflow.astream(
                input=initial_input,
                config=config,
                stream_mode=["messages", "values"],
            ):
                try:
                    event_type, event_message = event
                    if event_type == "messages":
                        message, metadata = event_message
                        if (
                            isinstance(message, AIMessageChunk)
                            and message.tool_calls
                            and message.tool_call_chunks[0]["name"] != "ClassifyUserIntent"
                        ):
                            tool_name = message.tool_call_chunks[0]["name"]
                            message_yield = json.dumps(
                                {"type": "tool_call", "content": tool_name}, ensure_ascii=False
                            )
                            print(message_yield)
                            yield message_yield + "\n"

                        if metadata["langgraph_node"] in [
                            "primary_assistant",
                            "scheduling_agent",
                            "book_hotel_agent",
                        ]:
                            if message.content:
                                temp += message.content
                                message_yield = json.dumps(
                                    {"type": "message", "content": temp}, ensure_ascii=False
                                )
                                print(message_yield)
                                yield message_yield + "\n"
                    if event_type == "values":
                        last_output_state = event_message
                except Exception as e:
                    logger.error(f"Error processing stream event: {str(e)}")
                    yield json.dumps({"type": "error", "content": "Error processing response" + str(e)}, ensure_ascii=False) + "\n"
                    return

            if last_output_state is None:
                raise ValueError("No output state received from workflow")

            final_ai_output = last_output_state["messages"][-1].content
            final_intent = last_output_state["intent"]
            tool_name_important = last_output_state["tool_name"]

            final_response = json.dumps(
                {
                    "type": "final",
                    "content": final_ai_output,
                    "intent": final_intent,
                    "tool_name": tool_name_important,
                },
                ensure_ascii=False,
            )
            yield final_response

        except Exception as e:
            logger.error(f"Error in workflow stream processing: {str(e)}")
            yield json.dumps({"type": "error", "content": "Error processing chat stream" + str(e)}, ensure_ascii=False) + "\n"
            return

    except Exception as e:
        logger.error(f"Unexpected error in chat streaming: {str(e)}")
        yield json.dumps({"type": "error", "content": "An unexpected error occurred" + str(e)}, ensure_ascii=False) + "\n"
        return

    background_tasks.add_task(
        save_history, user["id"], human_message, final_ai_output, final_intent
    )


async def chat_streaming_no_login_function(
    data: Chat, background_tasks: BackgroundTasks
):
    try:
        human_message = data.message
        history = data.history
        lat = data.lat
        long = data.long
        language = data.language
        logger.info(f"Language: {language}")

        try:
            process_history = post_process_history(history) if history is not None else None
        except Exception as e:
            logger.error(f"Error processing chat history: {str(e)}")
            yield json.dumps({"type": "error", "content": "Error processing chat history"}, ensure_ascii=False) + "\n"
            return

        config = {
            "configurable": {
                "user_id": None,
                "user_email": None,
                "contact_number": None,
                "session_id": None,
                "lat": lat,
                "long": long,
            }
        }

        initial_input = {
            "messages": [("user", human_message)],
            "messages_history": process_history,
            "entry_message": None,
            "manual_save": False,
            "intent": data.intent,
            "language": language,
            "tool_name": None,
            "ever_leave_skill": False,
        }

        last_output_state = None
        temp = ""

        try:
            async for event in workflow.astream(
                input=initial_input,
                config=config,
                stream_mode=["messages", "values"],
            ):
                try:
                    event_type, event_message = event
                    if event_type == "messages":
                        message, metadata = event_message
                        if (
                            isinstance(message, AIMessageChunk)
                            and message.tool_calls
                            and message.tool_call_chunks[0]["name"] != "ClassifyUserIntent"
                        ):
                            tool_name = message.tool_call_chunks[0]["name"]
                            message_yield = json.dumps(
                                {"type": "tool_call", "content": tool_name}, ensure_ascii=False
                            )
                            print(message_yield)
                            yield message_yield + "\n"

                        if metadata["langgraph_node"] in [
                            "primary_assistant",
                            "scheduling_agent",
                            "book_hotel_agent",
                        ]:
                            if message.content:
                                temp += message.content
                                message_yield = json.dumps(
                                    {"type": "message", "content": temp}, ensure_ascii=False
                                )
                                print(message_yield)
                                yield message_yield + "\n"
                    if event_type == "values":
                        last_output_state = event_message
                except Exception as e:
                    logger.error(f"Error processing stream event: {str(e)}")
                    yield json.dumps({"type": "error", "content": "Error processing response" + str(e)}, ensure_ascii=False) + "\n"
                    return

            if last_output_state is None:
                raise ValueError("No output state received from workflow")

            final_ai_output = last_output_state["messages"][-1].content
            final_intent = last_output_state["intent"]
            tool_name_important = last_output_state["tool_name"]

            final_response = json.dumps(
                {
                    "type": "final",
                    "content": final_ai_output,
                    "intent": final_intent,
                    "tool_name": tool_name_important,
                },
                ensure_ascii=False,
            )
            yield final_response

        except Exception as e:
            logger.error(f"Error in workflow stream processing: {str(e)}")
            yield json.dumps({"type": "error", "content": "Error processing chat stream" + str(e)}, ensure_ascii=False) + "\n"
            return

    except Exception as e:
        logger.error(f"Unexpected error in chat streaming: {str(e)}")
        yield json.dumps({"type": "error", "content": "An unexpected error occurred" + str(e)}, ensure_ascii=False) + "\n"
        return


async def chat_function(user, data: Chat, background_tasks: BackgroundTasks):
    message = data.message
    history = data.history
    lat = data.lat
    long = data.long
    language = data.language
    logger.info(f"Language: {language}")
    process_history = post_process_history(history) if history is not None else None
    config = {
        "configurable": {
            "user_id": user["id"],
            "user_email": user["email"],
            "contact_number": user["contact_number"],
            "session_id": user["id"],
            "lat": lat,
            "long": long,
        }
    }
    # try:
    initial_input = {
        "messages": [("user", message)],
        "messages_history": process_history,
        "entry_message": None,
        "manual_save": False,
        "intent": data.intent,
        "language": language,
        "tool_name": None,
    }
    output = await workflow.ainvoke(initial_input, config)

    final_ai_output = output["messages"][-1].content
    final_intent = output["intent"]
    tool_name = output["tool_name"]

    if final_ai_output is None:
        return JSONResponse(
            content={"message": "Error in chat_function"}, status_code=500
        )
    background_tasks.add_task(
        save_history, user["id"], data.message, final_ai_output, final_intent
    )

    response_ouput = {
        "message": final_ai_output,
        "intent": final_intent,
        "tool_name": tool_name,
    }
    return JSONResponse(content=response_ouput, status_code=200)


async def get_intent_function(session_id):
    record = await chat_history_management_crud.read_one({"session_id": session_id})
    if record is None:
        return None

    return record["intent"]


async def get_history_function(user_id, background_tasks: BackgroundTasks):
    history = chat_messages_history(user_id, 50)
    try:
        history_messages = await get_key_redis(f"chat_history_{user_id}")
        history_messages = None
        if not history_messages:
            logger.info("History not found in redis")
            history_messages = await history.aget_messages()
            history_messages = [
                i.model_dump(include=["type", "content"]) for i in history_messages
            ]
            intent = await get_intent_function(user_id)
            logger.info(f"INTENT {intent}")
            result = {"message": history_messages, "intent": intent}
            background_tasks.add_task(
                set_key_redis, f"chat_history_{user_id}", str(result)
            )
            return result
        history_messages = eval(history_messages)
        return history_messages
    except Exception as e:
        logger.error(f"Error in get_history_function: {e}")
        return {"message": [], "intent": None}


async def list_chat_history_function(user_id: str):
    result = await chat_history_management_crud.read({"user_id": user_id})
    if result is None:
        return []
    result = [i["session_id"] for i in result]
    return result


async def delete_chat_history_function(session_id: str):
    history = chat_messages_history(session_id, 50)
    await history.aclear()
    return {"message": "Chat history has been deleted"}
