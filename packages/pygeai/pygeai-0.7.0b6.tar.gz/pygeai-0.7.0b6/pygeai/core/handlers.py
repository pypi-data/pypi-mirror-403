from pygeai.core.base.mappers import ErrorMapper


class ErrorHandler:

    @classmethod
    def has_errors(cls, response):
        """
        Check if the response contains errors.
        
        Handles both dict and string responses for backward compatibility.
        Optimized to reduce redundant dictionary lookups when response is a dict.
        
        :param response: Response (dict or string) to check
        :return: True if errors found, False otherwise
        """
        if "errors" in response or "error" in response:
            return True
        
        if not isinstance(response, dict):
            return False
        
        message = response.get("message")
        return (
            isinstance(message, list) and
            message and
            message[0].get("type") == "error"
        )

    @classmethod
    def extract_error(cls, response):
        """
        Extract and map error information from response.
        
        :param response: Response dictionary containing error
        :return: Mapped error object
        """
        if "errors" in response:
            result = ErrorMapper.map_to_error_list_response(response)
        elif "error" in response:
            result = ErrorMapper.map_to_error(response.get('error'))
        else:
            result = response

        return result
