import os
import itertools

_api_keys = []

# Fetch up to 20 API keys that might be defined in the environment.
_key_cycle = None

def load_api_keys():
    global _key_cycle
    for i in range(1, 21):
        # Check for GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key:
            _api_keys.append(key)

    # Fallback if no numbered keys are found, just use the default GEMINI_API_KEY if available
    if not _api_keys:
        fallback_key = os.getenv("GEMINI_API_KEY")
        if fallback_key:
            _api_keys.append(fallback_key)
        else:
            # Raise an error instead of adding a placeholder so we know an API key is missing
            raise ValueError("No Gemini API key found. Please define GEMINI_API_KEY or GEMINI_API_KEY_1 in your environment.")

    # Create an infinite iterator that cycles through the available keys
    _key_cycle = itertools.cycle(_api_keys)

def get_api_key() -> str:
    """
    Returns the next API key in the cycle defined in the environment.
    This helps balance and avoid rate-limiting issues.
    """
    global _key_cycle
    if _key_cycle is None:
        load_api_keys()
    return next(_key_cycle)

