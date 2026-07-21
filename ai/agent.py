import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from models.conversation import Conversation, ConversationMessage
from models.user_profile import UserProfile
from .prompts import SYSTEM_PROMPT, TITLES_SYSTEM_PROMPT
from .functions import (
    get_workouts,
    get_workout_details,
    get_streaks,
    get_goals,
    get_chart_data,
    create_workout,
    mark_rest_day,
    set_goal,
)
from utils import logger
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import StructuredTool

# Tool parameter schema definitions using Pydantic BaseModel
class GetWorkoutsInput(BaseModel):
    date_from: str = Field(description="The start date for the date range.")
    date_to: str = Field(description="The end date for the date range.")

class GetWorkoutDetailsInput(BaseModel):
    workout_id: str = Field(description="The ID of the workout to retrieve details for.")

class GetStreaksInput(BaseModel):
    pass

class GetGoalsInput(BaseModel):
    pass

class GetChartDataInput(BaseModel):
    metric: str = Field(description="The metric to display on the chart. Must be one of: totalSkips, avgSkipsPerMin, calories, trips")
    chart_type: str = Field(description="The type of chart to display. Must be one of: bar, area")
    time_range: str = Field(description="The time range for the chart data. Must be one of: 7d, 30d, 90d")

class CreateWorkoutInput(BaseModel):
    duration: int = Field(description="Duration of the workout in seconds.")
    total_skips: int = Field(description="Total number of skips during the workout.")
    date: Optional[str] = Field(None, description="Optional date of the workout in ISO format. Leave empty for the current date/time.")
    avg_skips_per_minute: Optional[float] = Field(None, description="Optional average skips per minute.")
    trips: Optional[int] = Field(0, description="Optional number of times tripped.")
    calories: Optional[float] = Field(None, description="Optional calories burned.")
    heart_rate_avg: Optional[int] = Field(None, description="Optional average heart rate.")
    heart_rate_max: Optional[int] = Field(None, description="Optional maximum heart rate.")
    notes: Optional[str] = Field(None, description="Optional textual notes.")

class MarkRestDayInput(BaseModel):
    date: str = Field(description="The date to mark as a rest day in 'YYYY-MM-DD' format.")

class SetGoalInput(BaseModel):
    name: str = Field(description="The name of the goal to set. Must be one of: daily_skips, weekly_skips, weekly_workouts, daily_calories, weekly_calories, weekly_duration, skip_rate_goal")
    value: float = Field(description="The value to set the goal to.")

def dummy_tool_func():
    pass

# Langchain tool definitions wrapping schemas
langchain_tools = [
    StructuredTool.from_function(
        func=dummy_tool_func,
        name="get_workouts",
        description="Fetch all workouts within a given date range.",
        args_schema=GetWorkoutsInput
    ),
    StructuredTool.from_function(
        func=dummy_tool_func,
        name="get_workout_details",
        description="Get the full details for one specific workout.",
        args_schema=GetWorkoutDetailsInput
    ),
    StructuredTool.from_function(
        func=dummy_tool_func,
        name="get_streaks",
        description="Get the current streak, the best streak, and the rest days.",
        args_schema=GetStreaksInput
    ),
    StructuredTool.from_function(
        func=dummy_tool_func,
        name="get_goals",
        description="Get an array of goals with their progress percentage.",
        args_schema=GetGoalsInput
    ),
    StructuredTool.from_function(
        func=dummy_tool_func,
        name="get_chart_data",
        description="Get the aggregated data series for charting workout metrics.",
        args_schema=GetChartDataInput
    ),
    StructuredTool.from_function(
        func=dummy_tool_func,
        name="create_workout",
        description="Create a new workout for the user based on provided metrics.",
        args_schema=CreateWorkoutInput
    ),
    StructuredTool.from_function(
        func=dummy_tool_func,
        name="mark_rest_day",
        description="Mark a specific date as a rest day.",
        args_schema=MarkRestDayInput
    ),
    StructuredTool.from_function(
        func=dummy_tool_func,
        name="set_goal",
        description="Set a specific goal for the user.",
        args_schema=SetGoalInput
    )
]

AVAILABLE_MODELS = {
    "claude": [
        "claude-sonnet-5",
        "claude-opus-4-8",
        "claude-sonnet-4-6",
        "claude-3-7-sonnet-latest"
    ],
    "chatgpt": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-03-mini",
        "gpt-5.5",
        "gpt-5.4",
        "gpt-5.4-mini"
    ],
    "gemini": [
        "gemini-1.5-flash",
        "gemini-2.5-flash",
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview",
        "gemini-2.5-pro",
        "gemma-4-31b"
    ],
    "groq": [
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "minimaxai/minimax-m2.7",
        "qwen/qwen3.6-27b"
    ],
    "grok": [
        "grok-2-latest",
        "grok-4.5",
        "grok-4.3"
    ]
}

def get_llm(user: UserProfile):
    """Instantiates the correct Langchain Chat Model based on user's provider and selected model."""
    provider = user.ai_provider
    api_key = user.api_key
    model = user.ai_model
    
    if not provider or not provider.strip():
        raise ValueError("AI provider is not configured for the user profile.")
    if not api_key or not api_key.strip():
        raise ValueError("API key is not configured for the user profile.")
        
    provider_lower = provider.lower().strip()
    
    if provider_lower == "claude":
        # Options: claude-sonnet-5, claude-opus-4-8, claude-sonnet-4-6, claude-3-7-sonnet-latest
        model_name = model if model else "claude-sonnet-5"
        
        mapping = {
            "claude-sonnet-5": "claude-3-5-sonnet-latest",
            "claude-opus-4-8": "claude-3-opus-20240229",
            "claude-sonnet-4-6": "claude-3-5-sonnet-20240620",
            "claude-3-7-sonnet-latest": "claude-3-7-sonnet-latest",
        }
        actual_model = mapping.get(model_name, model_name)
        
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=actual_model, anthropic_api_key=api_key, temperature=0)
        
    elif provider_lower == "chatgpt":
        # Options: gpt-4o, gpt-4o-mini, gpt-03-mini, gpt-5.5, gpt-5.4, gpt-5.4-mini
        model_name = model if model else "gpt-4o"
        
        mapping = {
            "gpt-03-mini": "o3-mini",
        }
        actual_model = mapping.get(model_name, model_name)
        
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=actual_model, openai_api_key=api_key, temperature=0)
        
    elif provider_lower == "gemini":
        # Options: gemma-4-31b, gemini-2.5-flash, gemini-3.5-flash, gemini-3.1-flash-lite, gemini-3.1-pro-preview, gemini-3-flash-preview, gemini-2.5-pro
        model_name = model if model else "gemini-1.5-flash"
        
        mapping = {
            "gemma-4-31b": "gemma-2-27b-it", # Fallback or pass exactly
        }
        actual_model = mapping.get(model_name, model_name)
        
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=actual_model, google_api_key=api_key, temperature=0)
        
    elif provider_lower == "groq":
        # Options: openai/gpt-oss-20b, openai/gpt-oss-120b, llama-3.3-70b-versatile, minimaxai/minimax-m2.7, qwen/qwen3.6-27b
        model_name = model if model else "llama-3.3-70b-versatile"
        
        from langchain_groq import ChatGroq
        return ChatGroq(model=model_name, api_key=api_key, temperature=0)
        
    elif provider_lower == "grok":
        # Options: grok-4.5, grok-4.3
        model_name = model if model else "grok-2-latest"
        
        from langchain_xai import ChatXAI
        return ChatXAI(model=model_name, xai_api_key=api_key, temperature=0)
        
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")

async def generate_conversation_title(message: str, user: Optional[UserProfile] = None) -> str:
    """Generates a title for a new conversation based on the first message."""
    if not user or not user.api_key or not user.ai_provider:
        return "New Chat"
    try:
        llm = get_llm(user)
        messages = [
            SystemMessage(content=TITLES_SYSTEM_PROMPT),
            HumanMessage(content=message)
        ]
        response = await llm.ainvoke(messages)
        return response.content.strip()
    except Exception as e:
        logger.error(f"Error generating title: {e}")
        return "New Chat"

async def get_or_create_conversation(message: str, user: UserProfile, conversation_id: Optional[str], db: Session, title: str = "") -> Conversation:
    """Finds an existing conversation or creates a new one, generating a title if necessary."""
    if conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            conversation = Conversation(id=conversation_id)
            conversation.user_sync_token = user.sync_token
            db.add(conversation)
            db.commit()
        else:
            conversation.user_sync_token = user.sync_token
            db.commit()
    else:
        conversation = Conversation()
        conversation.user_sync_token = user.sync_token
        db.add(conversation)
        
        if not title:
            conversation.title = await generate_conversation_title(message, user=user)
        else:
            conversation.title = title
        db.commit()
        
    return conversation

def load_chat_history_for_langchain(conversation: Conversation, db: Session) -> List[Any]:
    """Loads a conversation's messages from the database and formats them for the Langchain model."""
    messages = []
    db_messages = db.query(ConversationMessage).filter(ConversationMessage.conversation_id == conversation.id).order_by(ConversationMessage.created_at).all()
    
    last_tool_calls_map = {}
    
    for msg in db_messages:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "model":
            if msg.tool_calls:
                lc_tool_calls = []
                for idx, tc in enumerate(msg.tool_calls):
                    tc_id = f"call_{msg.id}_{idx}"
                    last_tool_calls_map[tc["name"]] = tc_id
                    lc_tool_calls.append({
                        "name": tc["name"],
                        "args": tc.get("args", {}),
                        "id": tc_id,
                        "type": "tool_call"
                    })
                messages.append(AIMessage(content=msg.content or "", tool_calls=lc_tool_calls))
            else:
                messages.append(AIMessage(content=msg.content))
        elif msg.role in ("tool", "function"):
            if msg.tool_results:
                for idx, tr in enumerate(msg.tool_results):
                    tc_id = last_tool_calls_map.get(tr["name"]) or f"call_fallback_{msg.id}_{idx}"
                    messages.append(ToolMessage(
                        content=json.dumps(tr["response"]),
                        name=tr["name"],
                        tool_call_id=tc_id
                    ))
    return messages

def save_conversation_message(conversation_id: str, role: str, db: Session, content: str = None, tool_calls: list = None, tool_results: list = None) -> ConversationMessage:
    """Helper to save a message to the database."""
    msg = ConversationMessage(
        conversation_id=conversation_id, 
        role=role, 
        content=content,
        tool_calls=tool_calls,
        tool_results=tool_results
    )
    db.add(msg)
    db.commit()
    return msg

async def execute_agent_tool(tool_name: str, args: Dict[str, Any], user: UserProfile):
    """Executes a single requested tool and returns the result."""
    logger.info("Executing Agent tool", extra={"tool_name": tool_name, "user_id": user.id})
    print(f"\n--- 🛠️ EXECUTING TOOL: {tool_name} ---")
    print(f"Arguments: {args}")

    args_dict = dict(args)
    args_dict["user_sync_token"] = user.sync_token

    if tool_name == "get_workouts":
        result = await asyncio.to_thread(get_workouts, **args_dict)
    elif tool_name == "get_workout_details":
        result = await asyncio.to_thread(get_workout_details, **args_dict)
    elif tool_name == "get_streaks":
        result = await asyncio.to_thread(get_streaks, **args_dict)
    elif tool_name == "get_goals":
        result = await asyncio.to_thread(get_goals, **args_dict)
    elif tool_name == "get_chart_data":
        result = await asyncio.to_thread(get_chart_data, **args_dict)
    elif tool_name == "create_workout":
        result = await asyncio.to_thread(create_workout, **args_dict)
    elif tool_name == "mark_rest_day":
        result = await asyncio.to_thread(mark_rest_day, **args_dict)
    elif tool_name == "set_goal":
        result = await asyncio.to_thread(set_goal, **args_dict)
    else:
        result = {"error": f"Unknown function: {tool_name}"}
        
    print(f"Result: {result}")
    print("-" * 40)
    return result

async def ask_agent(message: str, user: UserProfile, conversation: Conversation, db: Session = None, continue_conversation: bool = False):
    """
    Sends a message to the AI agent configured in the user profile using Langchain.
    """
    logger.info("Starting up Agent interaction", extra={"conversation_id": conversation.id, "user_id": user.id, "continue": continue_conversation})
    
    llm = get_llm(user)
    model_with_tools = llm.bind_tools(langchain_tools)
    
    messages = []
    
    if db:
        messages = load_chat_history_for_langchain(conversation, db)
        if not continue_conversation:
            save_conversation_message(conversation.id, "user", db, content=message)
            
    if not continue_conversation:
        messages.append(HumanMessage(content=message))
        
    system_message = SystemMessage(
        content=SYSTEM_PROMPT.format(now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    
    while True:
        logger.info("Sending request to Langchain Chat Model", extra={"context_length": len(messages), "conversation_id": conversation.id})
        print("\n" + "="*50)
        yield f"data: {json.dumps({'type': 'status', 'message': f'Sending request to {user.ai_provider}...'})}\n\n"
        print(f"📤 SENDING REQUEST TO {user.ai_provider.upper()}")
        print(f"Payload context length: {len(messages)} item(s)")
        print("="*50)
        
        # Invoke Langchain model with system prompt as the first message
        response = await model_with_tools.ainvoke([system_message] + messages)
        
        if not response.tool_calls:
            logger.info("Received final text response from Agent", extra={"conversation_id": conversation.id})
            print("\n" + "="*50)
            print("✅ RECEIVED FINAL TEXT RESPONSE")
            print(f"Response: {response.content}")
            print("="*50 + "\n")
            
            if db:
                save_conversation_message(conversation.id, "model", db, content=response.content)
                
            yield f"data: {json.dumps({'type': 'final_response', 'text': response.content})}\n\n"
            return
            
        logger.info("Received tool calls from Agent", extra={"conversation_id": conversation.id, "num_calls": len(response.tool_calls)})
        print("\n" + "="*50)
        print(f"⚙️ RECEIVED FUNCTION CALL REQUESTS ({len(response.tool_calls)})")
        print("="*50)
        
        if db:
            tool_calls_data = [{"name": tc["name"], "args": tc["args"]} for tc in response.tool_calls]
            save_conversation_message(conversation.id, "model", db, tool_calls=tool_calls_data)
            
        # Append AIMessage with its tool_calls to context history
        messages.append(response)
        
        tool_results_data = []
        
        for tc in response.tool_calls:
            yield f"data: {json.dumps({'type': 'tool_call', 'tool': tc['name'], 'args': tc['args']})}\n\n"
            
            result = await execute_agent_tool(tc["name"], tc["args"], user)
            
            yield f"data: {json.dumps({'type': 'tool_result', 'tool': tc['name'], 'result': result})}\n\n"
            
            # Construct a ToolMessage for Langchain
            messages.append(ToolMessage(
                content=json.dumps(result),
                name=tc["name"],
                tool_call_id=tc["id"]
            ))
            tool_results_data.append({"name": tc["name"], "response": result})
            
        if db:
            save_conversation_message(conversation.id, "function", db, tool_results=tool_results_data)
            
        # If any write tools were called, finish the request here so the client can handle approval
        if any(tc["name"] in ["create_workout", "mark_rest_day", "set_goal"] for tc in response.tool_calls):
            logger.info("Closing Agent stream after writing operations", extra={"conversation_id": conversation.id})
            yield f"data: {json.dumps({'type': 'close'})}\n\n"
            return
