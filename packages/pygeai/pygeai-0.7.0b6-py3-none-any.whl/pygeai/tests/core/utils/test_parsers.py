import unittest
from unittest.mock import Mock
from json import JSONDecodeError

from pygeai.core.utils.parsers import parse_json_response
from pygeai.core.common.exceptions import InvalidAPIResponseException


class TestParseJsonResponse(unittest.TestCase):
    """
    Comprehensive tests for parse_json_response() function.
    
    Run with:
        python -m unittest pygeai.tests.core.utils.test_parsers.TestParseJsonResponse
    """

    def test_parse_valid_json_simple(self):
        """Test parsing simple valid JSON response"""
        mock_response = Mock()
        mock_response.json.return_value = {"key": "value"}
        
        result = parse_json_response(mock_response, "test operation")
        
        self.assertEqual(result, {"key": "value"})
        mock_response.json.assert_called_once()

    def test_parse_valid_json_complex(self):
        """Test parsing complex nested JSON response"""
        complex_data = {
            "data": {
                "items": [1, 2, 3],
                "metadata": {
                    "count": 3,
                    "nested": {
                        "deep": "value"
                    }
                }
            },
            "status": "success"
        }
        mock_response = Mock()
        mock_response.json.return_value = complex_data
        
        result = parse_json_response(mock_response, "fetch data")
        
        self.assertEqual(result, complex_data)
        self.assertEqual(result["data"]["items"], [1, 2, 3])
        self.assertEqual(result["data"]["metadata"]["nested"]["deep"], "value")

    def test_parse_valid_json_empty_object(self):
        """Test parsing empty JSON object"""
        mock_response = Mock()
        mock_response.json.return_value = {}
        
        result = parse_json_response(mock_response, "test operation")
        
        self.assertEqual(result, {})

    def test_parse_valid_json_array(self):
        """Test parsing JSON array"""
        mock_response = Mock()
        mock_response.json.return_value = [1, 2, 3, 4, 5]
        
        result = parse_json_response(mock_response, "get list")
        
        self.assertEqual(result, [1, 2, 3, 4, 5])

    def test_parse_valid_json_null_values(self):
        """Test parsing JSON with null values"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "field1": None,
            "field2": "value",
            "field3": None
        }
        
        result = parse_json_response(mock_response, "test operation")
        
        self.assertIsNone(result["field1"])
        self.assertEqual(result["field2"], "value")
        self.assertIsNone(result["field3"])

    def test_parse_json_decode_error_no_context(self):
        """Test JSONDecodeError handling without context"""
        mock_response = Mock()
        mock_response.json.side_effect = JSONDecodeError("msg", "doc", 0)
        mock_response.status_code = 500
        mock_response.text = "Invalid JSON"
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            parse_json_response(mock_response, "get data")
        
        exception_msg = str(context.exception)
        self.assertIn("Unable to get data", exception_msg)
        self.assertIn("Invalid JSON", exception_msg)

    def test_parse_json_decode_error_single_context(self):
        """Test JSONDecodeError with single context parameter"""
        mock_response = Mock()
        mock_response.json.side_effect = JSONDecodeError("msg", "doc", 0)
        mock_response.status_code = 404
        mock_response.text = "Not found"
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            parse_json_response(
                mock_response, 
                "get agent", 
                agent_id="agent-123"
            )
        
        exception_msg = str(context.exception)
        self.assertIn("Unable to get agent 'agent-123'", exception_msg)
        self.assertIn("Not found", exception_msg)

    def test_parse_json_decode_error_multiple_context(self):
        """Test JSONDecodeError with multiple context parameters"""
        mock_response = Mock()
        mock_response.json.side_effect = JSONDecodeError("msg", "doc", 0)
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            parse_json_response(
                mock_response,
                "update agent",
                agent_id="agent-123",
                project_id="proj-456"
            )
        
        exception_msg = str(context.exception)
        self.assertIn("Unable to update agent", exception_msg)
        # Should contain both context values
        self.assertIn("agent-123", exception_msg)
        self.assertIn("proj-456", exception_msg)

    def test_parse_json_different_status_codes(self):
        """Test error handling with various HTTP status codes"""
        status_codes = [400, 401, 403, 404, 500, 502, 503]
        
        for status_code in status_codes:
            with self.subTest(status_code=status_code):
                mock_response = Mock()
                mock_response.json.side_effect = JSONDecodeError("msg", "doc", 0)
                mock_response.status_code = status_code
                mock_response.text = f"Error {status_code}"
                
                with self.assertRaises(InvalidAPIResponseException):
                    parse_json_response(mock_response, "test operation")

    def test_parse_json_special_characters(self):
        """Test parsing JSON with special characters"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "text": "Hello \"world\"",
            "unicode": "こんにちは",
            "symbols": "!@#$%^&*()",
            "newlines": "line1\nline2\nline3"
        }
        
        result = parse_json_response(mock_response, "test operation")
        
        self.assertEqual(result["text"], "Hello \"world\"")
        self.assertEqual(result["unicode"], "こんにちは")
        self.assertEqual(result["symbols"], "!@#$%^&*()")
        self.assertEqual(result["newlines"], "line1\nline2\nline3")

    def test_parse_json_large_numbers(self):
        """Test parsing JSON with large numbers"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "small": 1,
            "large_int": 9999999999999999,
            "float": 123.456789,
            "scientific": 1.23e-10
        }
        
        result = parse_json_response(mock_response, "test operation")
        
        self.assertEqual(result["small"], 1)
        self.assertEqual(result["large_int"], 9999999999999999)
        self.assertAlmostEqual(result["float"], 123.456789, places=6)

    def test_parse_json_boolean_values(self):
        """Test parsing JSON with boolean values"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "true_value": True,
            "false_value": False,
            "null_value": None
        }
        
        result = parse_json_response(mock_response, "test operation")
        
        self.assertTrue(result["true_value"])
        self.assertFalse(result["false_value"])
        self.assertIsNone(result["null_value"])

    def test_parse_json_empty_string_response(self):
        """Test handling of empty string JSON response"""
        mock_response = Mock()
        mock_response.json.side_effect = JSONDecodeError("Expecting value", "", 0)
        mock_response.status_code = 200
        mock_response.text = ""
        
        with self.assertRaises(InvalidAPIResponseException):
            parse_json_response(mock_response, "test operation")

    def test_parse_json_preserves_order(self):
        """Test that JSON parsing preserves data structure"""
        ordered_data = {
            "first": 1,
            "second": 2,
            "third": 3,
            "array": ["a", "b", "c"]
        }
        mock_response = Mock()
        mock_response.json.return_value = ordered_data
        
        result = parse_json_response(mock_response, "test operation")
        
        self.assertEqual(list(result.keys()), ["first", "second", "third", "array"])
        self.assertEqual(result["array"], ["a", "b", "c"])

    def test_parse_json_with_context_formatting(self):
        """Test that context formatting works correctly in error messages"""
        mock_response = Mock()
        mock_response.json.side_effect = JSONDecodeError("msg", "doc", 0)
        mock_response.status_code = 500
        mock_response.text = "Error"
        
        # Test with string context
        with self.assertRaises(InvalidAPIResponseException) as ctx:
            parse_json_response(mock_response, "operation", name="test")
        self.assertIn("'test'", str(ctx.exception))
        
        # Test with numeric context
        with self.assertRaises(InvalidAPIResponseException) as ctx:
            parse_json_response(mock_response, "operation", id=123)
        self.assertIn("'123'", str(ctx.exception))

    def test_parse_json_real_world_api_response(self):
        """Test parsing realistic API response structure"""
        api_response = {
            "id": "agent-123",
            "name": "Test Agent",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z",
            "metadata": {
                "version": "1.0",
                "tags": ["production", "critical"]
            },
            "config": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
        mock_response = Mock()
        mock_response.json.return_value = api_response
        
        result = parse_json_response(mock_response, "get agent", agent_id="agent-123")
        
        self.assertEqual(result["id"], "agent-123")
        self.assertEqual(result["name"], "Test Agent")
        self.assertEqual(result["metadata"]["version"], "1.0")
        self.assertEqual(len(result["metadata"]["tags"]), 2)
        self.assertEqual(result["config"]["temperature"], 0.7)


class TestParseJsonResponseEdgeCases(unittest.TestCase):
    """
    Edge case tests for parse_json_response()
    
    Run with:
        python -m unittest pygeai.tests.core.utils.test_parsers.TestParseJsonResponseEdgeCases
    """

    def test_response_json_method_not_callable(self):
        """Test behavior when response.json is not callable"""
        mock_response = Mock()
        mock_response.json = "not a method"
        
        with self.assertRaises(TypeError):
            parse_json_response(mock_response, "test operation")

    def test_response_without_json_method(self):
        """Test behavior when response has no json method"""
        mock_response = Mock(spec=[])  # No methods
        
        with self.assertRaises(AttributeError):
            parse_json_response(mock_response, "test operation")

    def test_json_method_raises_other_exception(self):
        """Test that non-JSONDecodeError exceptions are not caught"""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Some other error")
        
        # Should raise ValueError, not catch it
        with self.assertRaises(ValueError):
            parse_json_response(mock_response, "test operation")

    def test_extremely_nested_json(self):
        """Test parsing deeply nested JSON structure"""
        # Create deeply nested structure
        nested = {"level": 10}
        for i in range(9, 0, -1):
            nested = {"level": i, "nested": nested}
        
        mock_response = Mock()
        mock_response.json.return_value = nested
        
        result = parse_json_response(mock_response, "test operation")
        
        # Verify we can access deep nesting
        current = result
        for i in range(1, 11):
            self.assertEqual(current["level"], i)
            if i < 10:
                current = current["nested"]

    def test_json_with_mixed_types_in_array(self):
        """Test parsing array with mixed types"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "mixed": [1, "string", True, None, {"key": "value"}, [1, 2, 3]]
        }
        
        result = parse_json_response(mock_response, "test operation")
        
        self.assertEqual(result["mixed"][0], 1)
        self.assertEqual(result["mixed"][1], "string")
        self.assertTrue(result["mixed"][2])
        self.assertIsNone(result["mixed"][3])
        self.assertEqual(result["mixed"][4], {"key": "value"})
        self.assertEqual(result["mixed"][5], [1, 2, 3])

    def test_context_with_special_characters(self):
        """Test context parameters with special characters"""
        mock_response = Mock()
        mock_response.json.side_effect = JSONDecodeError("msg", "doc", 0)
        mock_response.status_code = 400
        mock_response.text = "Error"
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            parse_json_response(
                mock_response,
                "test operation",
                name="Agent's \"Special\" Name"
            )
        
        exception_msg = str(context.exception)
        self.assertIn("Unable to test operation", exception_msg)

    def test_response_text_with_html(self):
        """Test error message when response.text contains HTML"""
        mock_response = Mock()
        mock_response.json.side_effect = JSONDecodeError("msg", "doc", 0)
        mock_response.status_code = 500
        mock_response.text = "<html><body>Internal Server Error</body></html>"
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            parse_json_response(mock_response, "test operation")
        
        exception_msg = str(context.exception)
        self.assertIn("<html>", exception_msg)

    def test_multiple_calls_same_response(self):
        """Test that calling parse multiple times works correctly"""
        mock_response = Mock()
        mock_response.json.return_value = {"key": "value"}
        
        result1 = parse_json_response(mock_response, "operation 1")
        result2 = parse_json_response(mock_response, "operation 2")
        
        self.assertEqual(result1, result2)
        self.assertEqual(mock_response.json.call_count, 2)


if __name__ == '__main__':
    unittest.main()
