

class GEAIException(Exception):
    """Base class for all PyGEAI exceptions."""
    pass


class UnknownArgumentError(GEAIException):
    """Raised when an unknown or invalid command/option is provided"""
    
    def __init__(self, message: str, arg: str = None, available_commands=None, available_options=None):
        """
        Initialize an UnknownArgumentError with context.
        
        :param message: str - The error message.
        :param arg: str - The unknown argument that was provided.
        :param available_commands: list - Available commands for suggestion.
        :param available_options: list - Available options for suggestion.
        """
        super().__init__(message)
        self.arg = arg
        self.available_commands = available_commands
        self.available_options = available_options


class MissingRequirementException(GEAIException):
    """Raised when a required parameter or argument is missing"""
    pass


class WrongArgumentError(GEAIException):
    """Raised when arguments are incorrectly formatted or invalid"""
    pass


class ValidationError(WrongArgumentError):
    """
    Raised when input validation fails with detailed context.
    
    Extends WrongArgumentError to provide structured validation errors
    with field-specific information and examples.
    """
    def __init__(
        self, 
        message: str, 
        field: str = None, 
        expected: str = None,
        received: str = None,
        example: str = None
    ):
        """
        Initialize a ValidationError with detailed context.

        :param message: str - The main error message.
        :param field: str - Name of the field that failed validation.
        :param expected: str - Description of what was expected.
        :param received: str - Description of what was received.
        :param example: str - Example of valid input.
        """
        super().__init__(message)
        self.field = field
        self.expected = expected
        self.received = received
        self.example = example
    
    def __str__(self) -> str:
        """
        Format the error message with all available context.

        :return: str - Formatted error message with field details.
        """
        parts = [super().__str__()]
        
        if self.field:
            parts.append(f"  Field: {self.field}")
        if self.expected:
            parts.append(f"  Expected: {self.expected}")
        if self.received:
            parts.append(f"  Received: {self.received}")
        if self.example:
            parts.append(f"  Example: {self.example}")
            
        return "\n".join(parts)


class ServerResponseError(GEAIException):
    """Raised when the server returns an error response"""
    pass


class APIError(GEAIException):
    """Raised when an API request fails"""
    pass


class InvalidPathException(GEAIException):
    """Raised when a file or directory path is invalid or not found"""
    pass


class InvalidJSONException(GEAIException):
    """Raised when JSON data cannot be parsed or is malformed"""
    pass


class InvalidAPIResponseException(GEAIException):
    """Raised when the API response format is unexpected or invalid"""
    pass


class InvalidResponseException(GEAIException):
    """Raised when a response cannot be retrieved or processed"""
    pass


class InvalidAgentException(GEAIException):
    """Raised when an agent cannot be retrieved, validated, or is misconfigured"""
    pass


class APIResponseError(GEAIException):
    """Raised when there is an error in the API response"""
    pass


class MixedAuthenticationException(GEAIException):
    """Raised when both API token and Oauth2 authentication are setup for the same profile"""
    pass


