from google import genai
from google.genai import types
from .system import SYSTEM_PROMPT
from .tools import (
    get_workouts_declaration,
    get_workout_details_declaration,
    get_streaks_declaration,
    get_goals_declaration,
    get_chart_data_declaration,
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

def ask_gemini(message: str):
    """
    Sends a message to the Gemini API using the Gemini 3 Flash Preview model.
    Passes the predefined system prompt along with the user message.
    """
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[gemini_tools],
        )
    )

    if response.function_calls:
        return response.function_calls
        
    return response.text
