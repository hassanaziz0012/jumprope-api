import asyncio
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from google import genai
from google.genai import types, errors
from models.conversation import Conversation, ConversationMessage
from models.user_profile import UserProfile
from .prompts import SYSTEM_PROMPT, TITLES_SYSTEM_PROMPT
from .tools import (
    get_workouts_declaration,
    get_workout_details_declaration,
    get_streaks_declaration,
    get_goals_declaration,
    get_chart_data_declaration,
    create_workout_declaration,
    mark_rest_day_declaration,
    set_goal_declaration,
)
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
from .cycle_keys import get_api_key
from utils import logger

gemini_tools = types.Tool(
    function_declarations=[
        get_workouts_declaration,
        get_workout_details_declaration,
        get_streaks_declaration,
        get_goals_declaration,
        get_chart_data_declaration,
        create_workout_declaration,
        mark_rest_day_declaration,
        set_goal_declaration,
    ]
)

async def generate_conversation_title(message: str) -> str:
    """Generates a title for a new conversation based on the first message."""
    client = genai.Client(api_key=get_api_key())
    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model='gemini-3-flash-preview',
            contents=[message],
            config=types.GenerateContentConfig(
                system_instruction=TITLES_SYSTEM_PROMPT,
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error generating title: {e}")
        return "New Chat"

async def get_or_create_conversation(message: str, user: UserProfile, conversation_id: Optional[str], db: Session) -> Conversation:
    """Finds an existing conversation or creates a new one, generating a title if necessary."""
    if conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            conversation = Conversation(id=conversation_id)
            conversation.user_sync_token = user.sync_token
            db.add(conversation)
            db.commit()
        else:
            # Ensure the existing conversation has the sync token assigned
            conversation.user_sync_token = user.sync_token
            db.commit()
    else:
        conversation = Conversation()
        conversation.user_sync_token = user.sync_token
        db.add(conversation)
        
        # Generate title
        title = await generate_conversation_title(message)
        conversation.title = title
        
        db.commit()
        
    return conversation

def load_chat_history_for_gemini(conversation: Conversation, db: Session) -> list[types.Content]:
    """Loads a conversation's messages from the database and formats them for the Gemini API."""
    contents = []
    db_messages = db.query(ConversationMessage).filter(ConversationMessage.conversation_id == conversation.id).order_by(ConversationMessage.created_at).all()
    for msg in db_messages:
        if msg.role == "user":
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=msg.content)]))
        elif msg.role == "model":
            if msg.tool_calls:
                function_calls = []
                for tc in msg.tool_calls:
                    args = tc.get("args", {})
                    function_calls.append(types.FunctionCall(name=tc["name"], args=args))
                contents.append(types.Content(role="model", parts=[types.Part.from_function_call(name=tc["name"], args=args) for tc in msg.tool_calls]))
            else:
                contents.append(types.Content(role="model", parts=[types.Part.from_text(text=msg.content)]))
        elif msg.role in ("tool", "function"):
            if msg.tool_results:
                function_responses = []
                for tr in msg.tool_results:
                    function_responses.append(types.Part.from_function_response(name=tr["name"], response={"result": tr["response"]}))
                contents.append(types.Content(role="user", parts=function_responses))
    return contents

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

async def execute_gemini_tool(tool_call, user: UserProfile):
    """Executes a single requested tool and returns the result."""
    args = tool_call.args if tool_call.args else {}
    logger.info("Executing Gemini tool", extra={"tool_name": tool_call.name, "user_id": user.id})
    print(f"\n--- 🛠️ EXECUTING TOOL: {tool_call.name} ---")
    print(f"Arguments: {args}")
    
    if tool_call.name == "get_workouts":
        result = await asyncio.to_thread(get_workouts, **args)
    elif tool_call.name == "get_workout_details":
        result = await asyncio.to_thread(get_workout_details, **args)
    elif tool_call.name == "get_streaks":
        result = await asyncio.to_thread(get_streaks, **args)
    elif tool_call.name == "get_goals":
        result = await asyncio.to_thread(get_goals, **args)
    elif tool_call.name == "get_chart_data":
        result = await asyncio.to_thread(get_chart_data, **args)
    elif tool_call.name == "create_workout":
        args_dict = dict(args)
        args_dict["user_profile_id"] = user.id
        result = await asyncio.to_thread(create_workout, **args_dict)
    elif tool_call.name == "mark_rest_day":
        args_dict = dict(args)
        args_dict["user_profile_id"] = user.id
        result = await asyncio.to_thread(mark_rest_day, **args_dict)
    elif tool_call.name == "set_goal":
        args_dict = dict(args)
        args_dict["user_profile_id"] = user.id
        result = await asyncio.to_thread(set_goal, **args_dict)
    else:
        result = {"error": f"Unknown function: {tool_call.name}"}
        
    print(f"Result: {result}")
    print("-" * 40)
    return result

async def generate_gemini_response(client: genai.Client, contents: list, yield_func) -> types.GenerateContentResponse:
    """Wraps the Gemini API call with retry logic for rate limits."""
    while True:
        try:
            return await asyncio.to_thread(
                client.models.generate_content,
                model='gemini-3-flash-preview',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT.format(now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    tools=[gemini_tools],
                )
            )
        except errors.APIError as e:
            if e.code == 503:
                await yield_func(f"data: {json.dumps({'type': 'status', 'message': 'The upstream AI provider is currently experiencing high demand and we will keep retrying. Delays are expected.'})}\n\n")
                await asyncio.sleep(2)
                continue
            raise e

async def ask_gemini(message: str, user: UserProfile, conversation_id: Optional[str] = None, db: Session = None, continue_conversation: bool = False):
    """
    Sends a message to the Gemini API using the Gemini 3 Flash Preview model.
    Passes the predefined system prompt along with the user message.
    """
    logger.info("Starting up Gemini interaction", extra={"conversation_id": conversation_id, "user_id": user.id, "continue": continue_conversation})
    client = genai.Client(api_key=get_api_key())
    contents = []
    
    if db:
        conversation = await get_or_create_conversation(message, user, conversation_id, db)
        yield f"data: {json.dumps({'type': 'conversation_id', 'id': conversation.id, 'title': conversation.title})}\n\n"
        
        contents = load_chat_history_for_gemini(conversation, db)
        if not continue_conversation:
            save_conversation_message(conversation.id, "user", db, content=message)
            
    if not continue_conversation:
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))
    
    async def yield_status(data: str):
        # A helper for passing yield back to generate_gemini_response for streaming messages
        yield data
    
    while True:
        logger.info("Sending request to Gemini API", extra={"context_length": len(contents), "conversation_id": conversation_id})
        print("\n" + "="*50)
        yield f"data: {json.dumps({'type': 'status', 'message': 'Sending request to Gemini...'})}\n\n"
        print("📤 SENDING REQUEST TO GEMINI")
        print(f"Payload context length: {len(contents)} item(s)")
        print(f"Payload: {contents}")
        print("="*50)
        
        try:
            response = await generate_gemini_response(client, contents, yield_status)
        except errors.APIError as e:
            if e.code == 429:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Quota exceeded; retrying with fresh quota.'})}\n\n"
                client = genai.Client(api_key=get_api_key())
                continue
            raise e
        
        if not response.function_calls:
            logger.info("Received final text response from Gemini", extra={"conversation_id": conversation_id})
            print("\n" + "="*50)
            print("✅ RECEIVED FINAL TEXT RESPONSE")
            print(f"Response: {response.text}")
            print("="*50 + "\n")
            
            if db:
                save_conversation_message(conversation.id, "model", db, content=response.text)
                
            yield f"data: {json.dumps({'type': 'final_response', 'text': response.text})}\n\n"
            return
            
        logger.info("Received function calls from Gemini", extra={"conversation_id": conversation_id, "num_calls": len(response.function_calls)})
        print("\n" + "="*50)
        print(f"⚙️ RECEIVED FUNCTION CALL REQUESTS ({len(response.function_calls)})")
        print("="*50)
        
        if db:
            tool_calls_data = [{"name": fc.name, "args": fc.args} for fc in response.function_calls]
            save_conversation_message(conversation.id, "model", db, tool_calls=tool_calls_data)
            
        # Append the content from the model's response
        contents.append(response.candidates[0].content)
        
        function_response_parts = []
        tool_results_data = []
        
        for tool_call in response.function_calls:
            args = tool_call.args if tool_call.args else {}
            yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_call.name, 'args': args})}\n\n"
            
            result = await execute_gemini_tool(tool_call, user)
            
            yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_call.name, 'result': result})}\n\n"
            
            function_response_part = types.Part.from_function_response(
                name=tool_call.name,
                response={"result": result},
            )
            function_response_parts.append(function_response_part)
            tool_results_data.append({"name": tool_call.name, "response": result})
            
        if db:
            save_conversation_message(conversation.id, "function", db, tool_results=tool_results_data)
            
        # Append the function responses
        contents.append(types.Content(role="user", parts=function_response_parts))
        
        # If any write tools were called, finish the request here so the client can handle approval
        if any(tc.name in ["create_workout", "mark_rest_day", "set_goal"] for tc in response.function_calls):
            logger.info("Closing Gemini stream after writing operations", extra={"conversation_id": conversation_id})
            yield f"data: {json.dumps({'type': 'close'})}\n\n"
            return
