import asyncio
import json
from datetime import datetime
from google import genai
from google.genai import types, errors
from .system import SYSTEM_PROMPT
from .tools import (
    get_workouts_declaration,
    get_workout_details_declaration,
    get_streaks_declaration,
    get_goals_declaration,
    get_chart_data_declaration,
)
from .functions import (
    get_workouts,
    get_workout_details,
    get_streaks,
    get_goals,
    get_chart_data
)
from .cycle_keys import get_api_key

gemini_tools = types.Tool(
    function_declarations=[
        get_workouts_declaration,
        get_workout_details_declaration,
        get_streaks_declaration,
        get_goals_declaration,
        get_chart_data_declaration,
    ]
)

async def ask_gemini(message: str):
    """
    Sends a message to the Gemini API using the Gemini 3 Flash Preview model.
    Passes the predefined system prompt along with the user message.
    """
    client = genai.Client(api_key=get_api_key())
    
    contents = [message]
    
    while True:
        print("\n" + "="*50)
        yield f"data: {json.dumps({'type': 'status', 'message': 'Sending request to Gemini...'})}\n\n"
        print("📤 SENDING REQUEST TO GEMINI")
        print(f"Payload context length: {len(contents)} item(s)")
        print(f"Payload: {contents}")
        print("="*50)
        
        try:
            response = await asyncio.to_thread(
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
                yield f"data: {json.dumps({'type': 'status', 'message': 'The upstream AI provider is currently experiencing high demand and we will keep retrying. Delays are expected.'})}\n\n"
                await asyncio.sleep(2)
                continue
            raise e
        
        if not response.function_calls:
            print("\n" + "="*50)
            print("✅ RECEIVED FINAL TEXT RESPONSE")
            print(f"Response: {response.text}")
            print("="*50 + "\n")
            yield f"data: {json.dumps({'type': 'final_response', 'text': response.text})}\n\n"
            return
            
        print("\n" + "="*50)
        print(f"⚙️ RECEIVED FUNCTION CALL REQUESTS ({len(response.function_calls)})")
        print("="*50)
            
        # Append the content from the model's response
        contents.append(response.candidates[0].content)
        
        function_response_parts = []
        for tool_call in response.function_calls:
            result = None
            args = tool_call.args if tool_call.args else {}
            
            print(f"\n--- 🛠️ EXECUTING TOOL: {tool_call.name} ---")
            print(f"Arguments: {args}")
            yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_call.name, 'args': args})}\n\n"
            
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
            else:
                result = {"error": f"Unknown function: {tool_call.name}"}
                
            print(f"Result: {result}")
            print("-" * 40)
            yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_call.name, 'result': result})}\n\n"
            
            function_response_part = types.Part.from_function_response(
                name=tool_call.name,
                response={"result": result},
            )
            function_response_parts.append(function_response_part)
            
        # Append the function responses
        contents.append(types.Content(role="user", parts=function_response_parts))
