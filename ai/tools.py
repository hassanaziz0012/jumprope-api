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
