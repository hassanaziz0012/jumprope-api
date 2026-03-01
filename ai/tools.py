get_workouts_declaration = {
    "name": "get_workouts",
    "description": "Fetch all workouts within a given date range.",
    "parameters": {
        "type": "object",
        "properties": {
            "date_from": {
                "type": "string",
                "description": "The start date for the date range.",
            },
            "date_to": {
                "type": "string",
                "description": "The end date for the date range.",
            },
        },
        "required": ["date_from", "date_to"],
    },
}

get_workout_details_declaration = {
    "name": "get_workout_details",
    "description": "Get the full details for one specific workout.",
    "parameters": {
        "type": "object",
        "properties": {
            "workout_id": {
                "type": "string",
                "description": "The ID of the workout to retrieve details for.",
            },
        },
        "required": ["workout_id"],
    },
}

get_streaks_declaration = {
    "name": "get_streaks",
    "description": "Get the current streak, the best streak, and the rest days.",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

get_goals_declaration = {
    "name": "get_goals",
    "description": "Get an array of goals with their progress percentage.",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

get_chart_data_declaration = {
    "name": "get_chart_data",
    "description": "Get the aggregated data series for charting workout metrics.",
    "parameters": {
        "type": "object",
        "properties": {
            "metric": {
                "type": "string",
                "enum": ["totalSkips", "avgSkipsPerMin", "calories", "trips"],
                "description": "The metric to display on the chart.",
            },
            "chart_type": {
                "type": "string",
                "enum": ["bar", "area"],
                "description": "The type of chart to display.",
            },
            "time_range": {
                "type": "string",
                "enum": ["7d", "30d", "90d"],
                "description": "The time range for the chart data.",
            },
        },
        "required": ["metric", "chart_type", "time_range"],
    },
}

create_workout_declaration = {
    "name": "create_workout",
    "description": "Create a new workout for the user based on provided metrics.",
    "parameters": {
        "type": "object",
        "properties": {
            "duration": {
                "type": "integer",
                "description": "Duration of the workout in seconds.",
            },
            "total_skips": {
                "type": "integer",
                "description": "Total number of skips during the workout.",
            },
            "date": {
                "type": "string",
                "description": "Optional date of the workout in ISO format. Leave empty for the current date/time.",
            },
            "avg_skips_per_minute": {
                "type": "number",
                "description": "Optional average skips per minute.",
            },
            "trips": {
                "type": "integer",
                "description": "Optional number of times tripped.",
            },
            "calories": {
                "type": "number",
                "description": "Optional calories burned.",
            },
            "heart_rate_avg": {
                "type": "integer",
                "description": "Optional average heart rate.",
            },
            "heart_rate_max": {
                "type": "integer",
                "description": "Optional maximum heart rate.",
            },
            "notes": {
                "type": "string",
                "description": "Optional textual notes.",
            }
        },
        "required": ["duration", "total_skips"],
    },
}

mark_rest_day_declaration = {
    "name": "mark_rest_day",
    "description": "Mark a specific date as a rest day.",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "The date to mark as a rest day in 'YYYY-MM-DD' format.",
            },
        },
        "required": ["date"],
    },
}

set_goal_declaration = {
    "name": "set_goal",
    "description": "Set a specific goal for the user.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "enum": [
                    "daily_skips", "weekly_skips", "weekly_workouts", 
                    "daily_calories", "weekly_calories", "weekly_duration", 
                    "skip_rate_goal"
                ],
                "description": "The name of the goal to set.",
            },
            "value": {
                "type": "number",
                "description": "The value to set the goal to.",
            },
        },
        "required": ["name", "value"],
    },
}
