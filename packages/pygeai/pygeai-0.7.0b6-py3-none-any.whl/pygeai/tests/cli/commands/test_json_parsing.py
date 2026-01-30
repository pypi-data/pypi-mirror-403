import unittest
import json
from json import JSONDecodeError


class TestCLIJsonParsing(unittest.TestCase):
    """
    Tests for JSON parsing patterns used in CLI commands.
    
    These tests document the current behavior of json.loads() in CLI commands
    to ensure optimizations don't break functionality.
    
    Run with:
        python -m unittest pygeai.tests.cli.commands.test_json_parsing.TestCLIJsonParsing
    """

    def test_parse_json_list_valid(self):
        """Test parsing valid JSON list from CLI argument"""
        json_str = '["input1", "input2", "input3"]'
        
        result = json.loads(json_str)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertEqual(result, ["input1", "input2", "input3"])

    def test_parse_json_dict_valid(self):
        """Test parsing valid JSON dict from CLI argument"""
        json_str = '{"key": "output_key", "description": "Output description"}'
        
        result = json.loads(json_str)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["key"], "output_key")
        self.assertEqual(result["description"], "Output description")

    def test_parse_json_list_of_dicts(self):
        """Test parsing list of dictionaries (common CLI pattern)"""
        json_str = '[{"key": "out1", "description": "First"}, {"key": "out2", "description": "Second"}]'
        
        result = json.loads(json_str)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["key"], "out1")
        self.assertEqual(result[1]["key"], "out2")

    def test_parse_json_invalid_raises_decode_error(self):
        """Test that invalid JSON raises JSONDecodeError"""
        invalid_json = 'not valid json'
        
        with self.assertRaises(JSONDecodeError):
            json.loads(invalid_json)

    def test_parse_json_empty_string_raises_error(self):
        """Test that empty string raises JSONDecodeError"""
        with self.assertRaises(JSONDecodeError):
            json.loads('')

    def test_parse_json_single_quoted_invalid(self):
        """Test that single quotes are invalid JSON (common CLI mistake)"""
        # Common mistake: using single quotes instead of double quotes
        invalid_json = "{'key': 'value'}"
        
        with self.assertRaises(JSONDecodeError):
            json.loads(invalid_json)

    def test_parse_json_trailing_comma_invalid(self):
        """Test that trailing commas are invalid JSON"""
        invalid_json = '{"key": "value",}'
        
        with self.assertRaises(JSONDecodeError):
            json.loads(invalid_json)

    def test_parse_json_unquoted_keys_invalid(self):
        """Test that unquoted keys are invalid JSON"""
        invalid_json = '{key: "value"}'
        
        with self.assertRaises(JSONDecodeError):
            json.loads(invalid_json)

    def test_parse_json_with_escaped_quotes(self):
        """Test parsing JSON with escaped quotes (common in CLI)"""
        json_str = '{"text": "He said \\"hello\\""}'
        
        result = json.loads(json_str)
        
        self.assertEqual(result["text"], 'He said "hello"')

    def test_parse_json_with_newlines(self):
        """Test parsing JSON with newlines"""
        json_str = '{\n  "key": "value",\n  "another": "test"\n}'
        
        result = json.loads(json_str)
        
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["another"], "test")

    def test_parse_json_boolean_values(self):
        """Test parsing JSON boolean values (lowercase only in JSON)"""
        json_str = '{"enabled": true, "disabled": false}'
        
        result = json.loads(json_str)
        
        self.assertTrue(result["enabled"])
        self.assertFalse(result["disabled"])

    def test_parse_json_null_value(self):
        """Test parsing JSON null value"""
        json_str = '{"value": null}'
        
        result = json.loads(json_str)
        
        self.assertIsNone(result["value"])

    def test_parse_json_numbers(self):
        """Test parsing various number formats"""
        json_str = '{"int": 42, "float": 3.14, "negative": -10, "scientific": 1e5}'
        
        result = json.loads(json_str)
        
        self.assertEqual(result["int"], 42)
        self.assertAlmostEqual(result["float"], 3.14)
        self.assertEqual(result["negative"], -10)
        self.assertEqual(result["scientific"], 100000)

    def test_parse_json_nested_structures(self):
        """Test parsing nested JSON structures (common in complex CLI args)"""
        json_str = '''
        {
            "agent": {
                "name": "Test Agent",
                "config": {
                    "inputs": ["input1", "input2"],
                    "outputs": [{"key": "out1", "type": "string"}]
                }
            }
        }
        '''
        
        result = json.loads(json_str)
        
        self.assertEqual(result["agent"]["name"], "Test Agent")
        self.assertEqual(len(result["agent"]["config"]["inputs"]), 2)
        self.assertEqual(result["agent"]["config"]["outputs"][0]["key"], "out1")

    def test_parse_json_empty_structures(self):
        """Test parsing empty JSON structures"""
        # Empty list
        result = json.loads('[]')
        self.assertEqual(result, [])
        
        # Empty dict
        result = json.loads('{}')
        self.assertEqual(result, {})

    def test_parse_json_unicode_characters(self):
        """Test parsing JSON with unicode characters"""
        json_str = '{"text": "Hello 世界 🌍"}'
        
        result = json.loads(json_str)
        
        self.assertEqual(result["text"], "Hello 世界 🌍")

    def test_parse_json_whitespace_handling(self):
        """Test that JSON parsing handles various whitespace correctly"""
        # Multiple spaces
        result1 = json.loads('  {  "key"  :  "value"  }  ')
        self.assertEqual(result1, {"key": "value"})
        
        # Tabs
        result2 = json.loads('\t{\t"key"\t:\t"value"\t}\t')
        self.assertEqual(result2, {"key": "value"})

    def test_isinstance_check_list(self):
        """Test isinstance check pattern used in CLI code"""
        result = json.loads('["a", "b"]')
        
        # This is the pattern used in CLI commands
        if isinstance(result, list):
            self.assertTrue(True)
        else:
            self.fail("Expected list type")

    def test_isinstance_check_dict(self):
        """Test isinstance check pattern for dict"""
        result = json.loads('{"key": "value"}')
        
        if isinstance(result, dict):
            self.assertTrue(True)
        else:
            self.fail("Expected dict type")

    def test_type_validation_pattern(self):
        """Test the type validation pattern used in CLI commands"""
        # Pattern: parse and validate type
        json_str = '["input1", "input2"]'
        
        try:
            result = json.loads(json_str)
            if not isinstance(result, list):
                raise ValueError("Expected list")
            # Success
            self.assertEqual(len(result), 2)
        except (JSONDecodeError, ValueError) as e:
            self.fail(f"Unexpected error: {e}")

    def test_dict_or_list_pattern(self):
        """Test the pattern where both dict and list are accepted"""
        # This pattern is common in CLI commands
        
        # Test with dict
        dict_str = '{"key": "value"}'
        result1 = json.loads(dict_str)
        self.assertTrue(isinstance(result1, (dict, list)))
        
        # Test with list
        list_str = '[{"key": "value"}]'
        result2 = json.loads(list_str)
        self.assertTrue(isinstance(result2, (dict, list)))


class TestCLIJsonParsingRealWorldCases(unittest.TestCase):
    """
    Real-world JSON parsing cases from CLI commands.
    
    Run with:
        python -m unittest pygeai.tests.cli.commands.test_json_parsing.TestCLIJsonParsingRealWorldCases
    """

    def test_agent_prompt_inputs_format(self):
        """Test agent_data_prompt_input format"""
        json_str = '["user_input", "context", "history"]'
        
        result = json.loads(json_str)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        for item in result:
            self.assertIsInstance(item, str)

    def test_agent_prompt_outputs_format(self):
        """Test agent_data_prompt_output format"""
        json_str = '[{"key": "response", "description": "Agent response"}, {"key": "confidence", "description": "Confidence score"}]'
        
        result = json.loads(json_str)
        
        self.assertIsInstance(result, list)
        for item in result:
            self.assertIn("key", item)
            self.assertIn("description", item)

    def test_agent_examples_format(self):
        """Test agent_data_prompt_example format"""
        json_str = '''
        [
            {
                "inputs": {"user_input": "Hello"},
                "output": {"response": "Hi there!"}
            }
        ]
        '''
        
        result = json.loads(json_str)
        
        self.assertIsInstance(result, list)
        self.assertIn("inputs", result[0])
        self.assertIn("output", result[0])

    def test_localized_description_format(self):
        """Test localized_description format"""
        json_str = '{"language": "en", "description": "Test description"}'
        
        result = json.loads(json_str)
        
        self.assertIsInstance(result, dict)
        self.assertIn("language", result)
        self.assertIn("description", result)

    def test_json_schema_format(self):
        """Test JSON schema format used in CLI"""
        json_str = '''
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        '''
        
        result = json.loads(json_str)
        
        self.assertEqual(result["type"], "object")
        self.assertIn("properties", result)
        self.assertIn("required", result)

    def test_tool_parameters_format(self):
        """Test tool parameters JSON format"""
        json_str = '''
        {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"]
                }
            }
        }
        '''
        
        result = json.loads(json_str)
        
        self.assertEqual(result["type"], "object")
        self.assertIn("enum", result["properties"]["unit"])

    def test_metadata_format(self):
        """Test metadata JSON format"""
        json_str = '{"version": "1.0", "tags": ["prod", "critical"], "owner": "team-a"}'
        
        result = json.loads(json_str)
        
        self.assertEqual(result["version"], "1.0")
        self.assertIsInstance(result["tags"], list)

    def test_files_argument_format(self):
        """Test files argument JSON format from chat commands"""
        json_str = '[{"id": "file-1", "name": "doc.pdf"}, {"id": "file-2", "name": "image.png"}]'
        
        result = json.loads(json_str)
        
        self.assertIsInstance(result, list)
        for file_obj in result:
            self.assertIn("id", file_obj)
            self.assertIn("name", file_obj)

    def test_evaluation_dataset_format(self):
        """Test evaluation dataset JSON format"""
        json_str = '''
        {
            "test_cases": [
                {"input": "test1", "expected": "output1"},
                {"input": "test2", "expected": "output2"}
            ]
        }
        '''
        
        result = json.loads(json_str)
        
        self.assertIn("test_cases", result)
        self.assertEqual(len(result["test_cases"]), 2)


class TestCLIJsonParsingErrorHandling(unittest.TestCase):
    """
    Test error handling patterns in CLI JSON parsing.
    
    Run with:
        python -m unittest pygeai.tests.cli.commands.test_json_parsing.TestCLIJsonParsingErrorHandling
    """

    def test_catch_json_decode_error(self):
        """Test catching JSONDecodeError"""
        invalid_json = 'invalid'
        
        try:
            json.loads(invalid_json)
            self.fail("Should have raised JSONDecodeError")
        except JSONDecodeError as e:
            # This is expected
            self.assertIsInstance(e, JSONDecodeError)

    def test_catch_value_error_for_type_check(self):
        """Test catching ValueError for type validation"""
        json_str = '{"key": "value"}'
        
        try:
            result = json.loads(json_str)
            if not isinstance(result, list):
                raise ValueError("Expected list")
            self.fail("Should have raised ValueError")
        except ValueError as e:
            self.assertIn("Expected list", str(e))

    def test_catch_combined_exceptions(self):
        """Test catching both JSONDecodeError and ValueError"""
        test_cases = [
            ('invalid json', JSONDecodeError),
            ('{"valid": "json"}', ValueError)  # Wrong type
        ]
        
        for json_str, expected_error in test_cases:
            with self.subTest(json_str=json_str):
                try:
                    result = json.loads(json_str)
                    if not isinstance(result, list):
                        raise ValueError("Expected list")
                except (JSONDecodeError, ValueError) as e:
                    self.assertIsInstance(e, (JSONDecodeError, ValueError))

    def test_error_with_generic_exception(self):
        """Test catching generic Exception (pattern used in some CLI commands)"""
        invalid_json = 'invalid'
        
        try:
            json.loads(invalid_json)
            self.fail("Should have raised exception")
        except Exception as e:
            # Generic exception catch (less specific but used in CLI code)
            self.assertIsInstance(e, JSONDecodeError)


if __name__ == '__main__':
    unittest.main()
