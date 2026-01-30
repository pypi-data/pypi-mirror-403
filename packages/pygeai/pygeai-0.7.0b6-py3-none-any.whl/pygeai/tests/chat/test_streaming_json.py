import unittest
import json
from json import JSONDecodeError
from unittest.mock import MagicMock
from pygeai.chat.clients import ChatClient
from pygeai.core.common.exceptions import InvalidAPIResponseException


class TestStreamingJsonParsing(unittest.TestCase):
    """
    Tests for JSON parsing in streaming responses.
    
    These tests validate the current behavior of json.loads() in streaming
    generators to ensure optimizations don't break functionality.
    
    Run with:
        python -m unittest pygeai.tests.chat.test_streaming_json.TestStreamingJsonParsing
    """

    def setUp(self):
        """Set up test client"""
        self.client = ChatClient(api_key="test_key", base_url="test_url")
        self.client.api_service = MagicMock()

    def test_parse_streaming_chunk_valid(self):
        """Test parsing valid streaming JSON chunk"""
        chunk = '{"choices": [{"delta": {"content": "Hello"}}]}'
        
        result = json.loads(chunk)
        
        self.assertIn("choices", result)
        self.assertEqual(result["choices"][0]["delta"]["content"], "Hello")

    def test_parse_streaming_chunk_invalid(self):
        """Test that invalid streaming chunk raises JSONDecodeError"""
        chunk = 'invalid json'
        
        with self.assertRaises(JSONDecodeError):
            json.loads(chunk)

    def test_parse_streaming_chunk_empty_content(self):
        """Test parsing chunk with empty content field"""
        chunk = '{"choices": [{"delta": {"content": ""}}]}'
        
        result = json.loads(chunk)
        
        self.assertEqual(result["choices"][0]["delta"]["content"], "")

    def test_parse_streaming_chunk_no_content(self):
        """Test parsing chunk without content field"""
        chunk = '{"choices": [{"delta": {}}]}'
        
        result = json.loads(chunk)
        
        self.assertNotIn("content", result["choices"][0]["delta"])

    def test_parse_streaming_chunk_multiple_choices(self):
        """Test parsing chunk with multiple choices"""
        chunk = '{"choices": [{"delta": {"content": "A"}}, {"delta": {"content": "B"}}]}'
        
        result = json.loads(chunk)
        
        self.assertEqual(len(result["choices"]), 2)
        self.assertEqual(result["choices"][0]["delta"]["content"], "A")

    def test_stream_chat_generator_success(self):
        """Test stream_chat_generator with valid data"""
        streaming_data = [
            'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            'data: {"choices": [{"delta": {"content": " world"}}]}',
            'data: {"choices": [{"delta": {"content": "!"}}]}',
            'data: [DONE]'
        ]
        
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_chat_generator(mock_response))
        
        self.assertEqual(result, ["Hello", " world", "!"])

    def test_stream_chat_generator_skips_invalid_json(self):
        """Test that generator skips chunks with invalid JSON"""
        streaming_data = [
            'data: {"choices": [{"delta": {"content": "Valid"}}]}',
            'data: invalid json here',  # Should be skipped
            'data: {"choices": [{"delta": {"content": " content"}}]}',
            'data: [DONE]'
        ]
        
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_chat_generator(mock_response))
        
        # Should only get valid chunks
        self.assertEqual(result, ["Valid", " content"])

    def test_stream_chat_generator_skips_malformed_structure(self):
        """Test that generator skips chunks with malformed structure"""
        streaming_data = [
            'data: {"choices": [{"delta": {"content": "Good"}}]}',
            'data: {"no_choices": "here"}',  # Malformed - no choices
            'data: {"choices": []}',  # Empty choices
            'data: {"choices": [{"no_delta": "here"}]}',  # No delta
            'data: {"choices": [{"delta": {"content": " data"}}]}',
            'data: [DONE]'
        ]
        
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_chat_generator(mock_response))
        
        self.assertEqual(result, ["Good", " data"])

    def test_stream_chat_generator_done_signal(self):
        """Test that [DONE] signal stops iteration"""
        streaming_data = [
            'data: {"choices": [{"delta": {"content": "Before"}}]}',
            'data: [DONE]',
            'data: {"choices": [{"delta": {"content": "After"}}]}'  # Should not be processed
        ]
        
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_chat_generator(mock_response))
        
        # Should only get content before [DONE]
        self.assertEqual(result, ["Before"])

    def test_stream_chat_generator_non_data_lines(self):
        """Test that non-data lines are ignored"""
        streaming_data = [
            'event: start',
            'data: {"choices": [{"delta": {"content": "Content"}}]}',
            ': comment line',
            'data: {"choices": [{"delta": {"content": " here"}}]}',
            'data: [DONE]'
        ]
        
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_chat_generator(mock_response))
        
        self.assertEqual(result, ["Content", " here"])

    def test_stream_response_generator_success(self):
        """Test stream_response_generator with valid data"""
        streaming_data = [
            'data: {"choices": [{"delta": {"content": "Test"}}]}',
            'data: {"choices": [{"delta": {"content": " response"}}]}',
            'data: [DONE]'
        ]
        
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_response_generator(mock_response))
        
        self.assertEqual(result, ["Test", " response"])

    def test_stream_generator_with_whitespace(self):
        """Test streaming with various whitespace in data"""
        streaming_data = [
            'data:  {"choices": [{"delta": {"content": "A"}}]}  ',  # Extra spaces
            'data:\t{"choices": [{"delta": {"content": "B"}}]}\t',  # Tabs
            'data:{"choices": [{"delta": {"content": "C"}}]}',  # No space after colon
            'data: [DONE]'
        ]
        
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_chat_generator(mock_response))
        
        self.assertEqual(result, ["A", "B", "C"])

    def test_stream_generator_error_handling(self):
        """Test that streaming errors are caught and raised appropriately"""
        def error_response():
            yield 'data: {"choices": [{"delta": {"content": "Start"}}]}'
            raise Exception("Streaming error")
        
        mock_response = error_response()
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            list(self.client.stream_chat_generator(mock_response))
        
        self.assertIn("Unable to process streaming chat response", str(context.exception))

    def test_streaming_chunk_with_special_characters(self):
        """Test streaming chunks with special characters"""
        chunk = '{"choices": [{"delta": {"content": "Hello \\"world\\" 🌍"}}]}'
        
        result = json.loads(chunk)
        
        self.assertEqual(result["choices"][0]["delta"]["content"], 'Hello "world" 🌍')

    def test_streaming_chunk_with_unicode(self):
        """Test streaming chunks with unicode characters"""
        chunk = '{"choices": [{"delta": {"content": "こんにちは世界"}}]}'
        
        result = json.loads(chunk)
        
        self.assertEqual(result["choices"][0]["delta"]["content"], "こんにちは世界")

    def test_streaming_chunk_with_newlines(self):
        """Test streaming chunks with newline characters"""
        chunk = '{"choices": [{"delta": {"content": "Line 1\\nLine 2\\nLine 3"}}]}'
        
        result = json.loads(chunk)
        
        self.assertEqual(result["choices"][0]["delta"]["content"], "Line 1\nLine 2\nLine 3")


class TestStreamingJsonParsingEdgeCases(unittest.TestCase):
    """
    Edge case tests for streaming JSON parsing.
    
    Run with:
        python -m unittest pygeai.tests.chat.test_streaming_json.TestStreamingJsonParsingEdgeCases
    """

    def setUp(self):
        """Set up test client"""
        self.client = ChatClient(api_key="test_key", base_url="test_url")
        self.client.api_service = MagicMock()

    def test_empty_streaming_response(self):
        """Test handling of empty streaming response"""
        streaming_data = []
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_chat_generator(mock_response))
        
        self.assertEqual(result, [])

    def test_only_done_signal(self):
        """Test streaming with only DONE signal"""
        streaming_data = ['data: [DONE]']
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_chat_generator(mock_response))
        
        self.assertEqual(result, [])

    def test_streaming_with_empty_chunks(self):
        """Test streaming with empty content chunks"""
        streaming_data = [
            'data: {"choices": [{"delta": {"content": ""}}]}',
            'data: {"choices": [{"delta": {"content": ""}}]}',
            'data: [DONE]'
        ]
        
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_chat_generator(mock_response))
        
        # Empty strings are still yielded
        self.assertEqual(result, ["", ""])

    def test_streaming_with_very_long_content(self):
        """Test streaming with very long content chunk"""
        long_content = "A" * 10000
        chunk = f'{{"choices": [{{"delta": {{"content": "{long_content}"}}}}]}}'
        streaming_data = [
            f'data: {chunk}',
            'data: [DONE]'
        ]
        
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_chat_generator(mock_response))
        
        self.assertEqual(len(result[0]), 10000)

    def test_streaming_with_nested_json_in_content(self):
        """Test streaming where content itself contains JSON string"""
        content = '{\\"nested\\": \\"value\\"}'
        chunk = f'{{"choices": [{{"delta": {{"content": "{content}"}}}}]}}'
        streaming_data = [
            f'data: {chunk}',
            'data: [DONE]'
        ]
        
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_chat_generator(mock_response))
        
        self.assertEqual(result[0], '{"nested": "value"}')

    def test_streaming_choices_out_of_bounds_protection(self):
        """Test that accessing choices[0] is safe"""
        # Chunk with empty choices array
        streaming_data = [
            'data: {"choices": []}',
            'data: [DONE]'
        ]
        
        mock_response = iter(streaming_data)
        
        # Should not raise IndexError - chunk should be skipped
        result = list(self.client.stream_chat_generator(mock_response))
        
        self.assertEqual(result, [])

    def test_streaming_delta_missing_content_key(self):
        """Test chunks where delta exists but no content key"""
        streaming_data = [
            'data: {"choices": [{"delta": {"role": "assistant"}}]}',  # No content
            'data: {"choices": [{"delta": {"content": "Valid"}}]}',
            'data: [DONE]'
        ]
        
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_chat_generator(mock_response))
        
        # Only chunk with content should be yielded
        self.assertEqual(result, ["Valid"])

    def test_streaming_multiple_rapid_chunks(self):
        """Test rapid succession of chunks (simulates fast streaming)"""
        streaming_data = [f'data: {{"choices": [{{"delta": {{"content": "{i}"}}}}]}}' for i in range(100)]
        streaming_data.append('data: [DONE]')
        
        mock_response = iter(streaming_data)
        
        result = list(self.client.stream_chat_generator(mock_response))
        
        self.assertEqual(len(result), 100)
        self.assertEqual(result[0], "0")
        self.assertEqual(result[99], "99")

    def test_streaming_chunk_access_pattern(self):
        """Test the nested dictionary access pattern used in streaming"""
        chunk = '{"choices": [{"delta": {"content": "test"}}]}'
        json_data = json.loads(chunk)
        
        # This is the exact pattern used in the code
        if (
            json_data.get("choices")
            and len(json_data["choices"]) > 0
            and "delta" in json_data["choices"][0]
            and "content" in json_data["choices"][0]["delta"]
        ):
            content = json_data["choices"][0]["delta"]["content"]
            self.assertEqual(content, "test")
        else:
            self.fail("Access pattern failed")

    def test_streaming_chunk_safe_get_pattern(self):
        """Test safe dictionary access with .get()"""
        # Test with valid structure
        chunk1 = '{"choices": [{"delta": {"content": "test"}}]}'
        data1 = json.loads(chunk1)
        choices = data1.get("choices")
        self.assertIsNotNone(choices)
        
        # Test with missing key
        chunk2 = '{"no_choices": []}'
        data2 = json.loads(chunk2)
        choices = data2.get("choices")
        self.assertIsNone(choices)


class TestStreamingJsonParsingPerformance(unittest.TestCase):
    """
    Performance-related tests for streaming JSON parsing.
    
    These tests ensure the current implementation can handle realistic scenarios.
    
    Run with:
        python -m unittest pygeai.tests.chat.test_streaming_json.TestStreamingJsonParsingPerformance
    """

    def test_parse_many_chunks_sequentially(self):
        """Test parsing many chunks in sequence (baseline performance test)"""
        chunks = [
            f'{{"choices": [{{"delta": {{"content": "chunk{i}"}}}}]}}'
            for i in range(1000)
        ]
        
        # Measure baseline performance
        for chunk in chunks:
            result = json.loads(chunk)
            self.assertIn("choices", result)

    def test_parse_complex_streaming_chunks(self):
        """Test parsing complex streaming chunks with nested data"""
        chunk = '''
        {
            "id": "chatcmpl-123",
            "object": "chat.completion.chunk",
            "created": 1694268190,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "delta": {
                    "role": "assistant",
                    "content": "Hello"
                },
                "finish_reason": null
            }]
        }
        '''
        
        result = json.loads(chunk)
        
        self.assertEqual(result["choices"][0]["delta"]["content"], "Hello")
        self.assertEqual(result["model"], "gpt-4")

    def test_parse_minimal_vs_verbose_chunks(self):
        """Test parsing both minimal and verbose chunk formats"""
        # Minimal
        minimal = '{"choices": [{"delta": {"content": "A"}}]}'
        result1 = json.loads(minimal)
        self.assertEqual(result1["choices"][0]["delta"]["content"], "A")
        
        # Verbose (more realistic from API)
        verbose = '''
        {
            "id": "123",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "model-name",
            "choices": [{
                "index": 0,
                "delta": {"content": "A"},
                "finish_reason": null
            }],
            "usage": null
        }
        '''
        result2 = json.loads(verbose)
        self.assertEqual(result2["choices"][0]["delta"]["content"], "A")


if __name__ == '__main__':
    unittest.main()
