from json import JSONDecodeError

from pygeai import logger
from pygeai.core.common.exceptions import InvalidAPIResponseException


def parse_json_response(response, operation: str, **context):
    """
    Parse JSON response with standardized error handling.

    Optimized to keep the hot path (success case) fast by separating
    error handling logic into a dedicated function.

    :param response: HTTP response object
    :param operation: Description of operation (e.g., "get project API token")
    :param context: Additional context (e.g., api_token_id="123")
    :return: Parsed JSON response
    :raises InvalidAPIResponseException: If JSON parsing fails
    """
    try:
        return response.json()
    except JSONDecodeError as e:
        _handle_json_parse_error(response, operation, context, e)


def _handle_json_parse_error(response, operation: str, context: dict, error: JSONDecodeError):
    """
    Handle JSON parsing errors with detailed error messages.
    
    Separated from main parsing function to optimize the hot path.
    This function is only called when parsing fails (rare case).
    
    :param response: HTTP response object
    :param operation: Description of operation
    :param context: Additional context parameters
    :param error: The JSONDecodeError that occurred
    :raises InvalidAPIResponseException: Always raises with detailed message
    """
    full_msg = f"Unable to {operation}"
    
    if context:
        if len(context) == 1:
            value = next(iter(context.values()))
            full_msg += f" '{value}'"
        else:
            context_str = ", ".join(f"{k}='{v}'" for k, v in context.items())
            full_msg += f" ({context_str})"
    
    logger.error(
        f"{full_msg}: JSON parsing error (status {response.status_code}): {error}. "
        f"Response: {response.text}"
    )
    raise InvalidAPIResponseException(f"{full_msg}: {response.text}")
