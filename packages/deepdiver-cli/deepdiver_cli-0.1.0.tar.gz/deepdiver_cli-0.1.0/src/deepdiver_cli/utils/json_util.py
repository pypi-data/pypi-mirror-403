import json


def is_incomplete_json(arguments: str) -> bool:
    """
    Check if JSON string is incomplete by attempting to parse it.

    Returns True if the JSON is incomplete or invalid,
    False if it can be successfully parsed as valid JSON.

    This is the most robust approach - it actually tries to parse the JSON
    rather than relying on heuristics like regex or brace counting.
    """
    if not arguments:
        return True

    try:
        # Try to parse as JSON
        json.loads(arguments)
        # If parsing succeeds, JSON is complete and valid
        return False
    except json.JSONDecodeError:
        # If parsing fails, JSON is incomplete or invalid
        return True