import json
from fastapi import BackgroundTasks
from src.langgraph.multi_agent.planner.planner_flow import planner_app
from src.utils.helper import parse_itinerary
from src.utils.logger import logger


async def message_generator(input_graph, config, background: BackgroundTasks):
    try:
        last_output_state = None
        temp = ""

        try:
            async for event in planner_app.astream(
                input=input_graph,
                config=config,
                stream_mode=["messages", "values"],
            ):
                try:
                    event_type, event_message = event
                    if event_type == "messages":
                        message, _ = event_message
                        if message.content:
                            temp += message.content
                            message_yield = json.dumps(
                                {"type": "message", "content": temp},
                                ensure_ascii=False,
                            )
                            yield message_yield + "\n\n"
                    if event_type == "values":
                        last_output_state = event_message
                except Exception as e:
                    logger.error(f"Error processing stream event: {str(e)}")
                    yield json.dumps({"type": "error", "content": "Error processing planner response " + str(e)}, ensure_ascii=False) + "\n\n"
                    return

            if last_output_state is None:
                raise ValueError("No output state received from planner workflow")

            if "final_answer" not in last_output_state:
                raise ValueError("No final answer in planner output")

            try:
                parser_ouput = parse_itinerary(last_output_state["final_answer"])
                final_response = json.dumps(
                    {
                        "type": "final",
                        "content": parser_ouput,
                    },
                    ensure_ascii=False,
                )
                yield final_response + "\n\n"
            except Exception as e:
                logger.error(f"Error parsing itinerary: {str(e)}")
                yield json.dumps({"type": "error", "content": "Error parsing the generated itinerary" + str(e)}, ensure_ascii=False) + "\n\n"
                return

        except Exception as e:
            logger.error(f"Error in planner workflow stream: {str(e)}")
            yield json.dumps({"type": "error", "content": "Error processing planner stream" + str(e)}, ensure_ascii=False) + "\n\n"
            return

    except Exception as e:
        logger.error(f"Unexpected error in planner: {str(e)}")
        yield json.dumps({"type": "error", "content": "An unexpected error occurred in the planner" + str(e)}, ensure_ascii=False) + "\n\n"
        return


from pydantic import BaseModel, Field
from datetime import datetime


class Activity(BaseModel):
    """Activity model"""

    description: str = Field(
        ..., description="Short description of the activity can have location"
    )
    start_time: datetime = Field(..., description="Start time of the activity")
    end_time: datetime = Field(..., description="End time of the activity")


class Output(BaseModel):
    """Output model"""

    activities: list[Activity] = Field(..., description="List of activities")
    note: str = Field(..., description="Note for the user")
