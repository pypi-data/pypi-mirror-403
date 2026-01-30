from pathlib import Path
from typing import Dict, List, Optional, Union
import json

from pygeai.core.common.exceptions import WrongArgumentError, ValidationError


def validate_dataset_file(dataset_file: str):
    path = Path(dataset_file)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_file}")
    if not path.is_file():
        raise ValueError(f"Dataset path is not a file: {dataset_file}")


def validate_row_structure(row: dict):
    required_fields = ["dataSetRowExpectedAnswer", "dataSetRowContextDocument", "dataSetRowInput"]
    for field in required_fields:
        if not isinstance(row.get(field), str):
            raise WrongArgumentError(f'Missing or invalid value for required field "{field}". It must be a non-empty string.')

    expected_sources = row.get("expectedSources", [])
    if not isinstance(expected_sources, list):
        raise WrongArgumentError('"expectedSources" must be a list of objects, even if empty.')
    for source in expected_sources:
        if not isinstance(source, dict) or not all(
                key in source and isinstance(source[key], str) for key in [
                    "dataSetExpectedSourceId", "dataSetExpectedSourceName",
                    "dataSetExpectedSourceValue", "dataSetExpectedSourceExtension"
                ]
        ):
            raise WrongArgumentError(
                'Each item in "expectedSources" must be a dictionary containing the following string fields: '
                '"dataSetExpectedSourceId", "dataSetExpectedSourceName", "dataSetExpectedSourceValue", and "dataSetExpectedSourceExtension".'
            )

    filter_variables = row.get("filterVariables", [])
    if not isinstance(filter_variables, list):
        raise WrongArgumentError('"filterVariables" must be a list of objects, even if empty.')
    for variable in filter_variables:
        if not isinstance(variable, dict) or not all(
                key in variable and isinstance(variable[key], str) for key in [
                    "dataSetMetadataType", "dataSetRowFilterKey",
                    "dataSetRowFilterOperator", "dataSetRowFilterValue", "dataSetRowFilterVarId"
                ]
        ):
            raise WrongArgumentError(
                'Each item in "filterVariables" must be a dictionary containing the following string fields: '
                '"dataSetMetadataType", "dataSetRowFilterKey", "dataSetRowFilterOperator", '
                '"dataSetRowFilterValue", and "dataSetRowFilterVarId".'
            )


def validate_system_metric(metric: dict):
    required_fields = ["systemMetricId", "systemMetricWeight"]

    if not isinstance(metric, dict):
        raise WrongArgumentError("Each system metric must be a dictionary.")

    for field in required_fields:
        if field not in metric:
            raise WrongArgumentError(f'Missing required field "{field}" in system metric.')

    if not isinstance(metric["systemMetricId"], str) or not metric["systemMetricId"].strip():
        raise WrongArgumentError('"systemMetricId" must be a non-empty string.')

    if not isinstance(metric["systemMetricWeight"], (int, float)) or not (0 <= metric["systemMetricWeight"] <= 1):
        raise WrongArgumentError('"systemMetricWeight" must be a number between 0 and 1 (inclusive).')


def validate_json_input(
    value: str, 
    expected_type: type,
    field_name: str,
    example: Optional[str] = None
) -> Union[Dict, List]:
    """
    Validates and parses JSON input with detailed error messages.

    :param value: str - The JSON string to parse.
    :param expected_type: type - Expected type (dict or list).
    :param field_name: str - Name of the field being validated.
    :param example: Optional[str] - Example of valid input.
    :return: Union[Dict, List] - Parsed JSON object.
    :raises ValidationError: If JSON is invalid or doesn't match expected type.
    """
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as e:
        raise ValidationError(
            f"Invalid JSON for '{field_name}'",
            field=field_name,
            expected="Valid JSON string",
            received=value[:100] + "..." if len(value) > 100 else value,
            example=example or '{"key": "value"}'
        ) from e
    
    if not isinstance(parsed, expected_type):
        raise ValidationError(
            f"Wrong type for '{field_name}'",
            field=field_name,
            expected=expected_type.__name__,
            received=type(parsed).__name__,
            example=example
        )
    
    return parsed


def validate_numeric_range(
    value: str,
    field_name: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    value_type: type = float
) -> Union[int, float]:
    """
    Validates numeric input within a specified range.

    :param value: str - The numeric string to validate.
    :param field_name: str - Name of the field being validated.
    :param min_value: Optional[float] - Minimum allowed value.
    :param max_value: Optional[float] - Maximum allowed value.
    :param value_type: type - Expected numeric type (int or float).
    :return: Union[int, float] - Validated numeric value.
    :raises ValidationError: If value is not numeric or out of range.
    """
    try:
        numeric_value = value_type(value)
    except ValueError as e:
        raise ValidationError(
            f"Invalid {value_type.__name__} for '{field_name}'",
            field=field_name,
            expected=f"{value_type.__name__}",
            received=value
        ) from e
    
    if min_value is not None and numeric_value < min_value:
        raise ValidationError(
            f"Value too low for '{field_name}'",
            field=field_name,
            expected=f">= {min_value}",
            received=str(numeric_value)
        )
    
    if max_value is not None and numeric_value > max_value:
        raise ValidationError(
            f"Value too high for '{field_name}'",
            field=field_name,
            expected=f"<= {max_value}",
            received=str(numeric_value)
        )
    
    return numeric_value


def validate_choice(
    value: str,
    field_name: str,
    choices: List[str],
    case_sensitive: bool = True
) -> str:
    """
    Validates that input is one of the allowed choices.

    :param value: str - The value to validate.
    :param field_name: str - Name of the field being validated.
    :param choices: List[str] - List of allowed values.
    :param case_sensitive: bool - Whether comparison is case-sensitive.
    :return: str - Validated value.
    :raises ValidationError: If value is not in choices.
    """
    compare_value = value if case_sensitive else value.lower()
    compare_choices = choices if case_sensitive else [c.lower() for c in choices]
    
    if compare_value not in compare_choices:
        raise ValidationError(
            f"Invalid value for '{field_name}'",
            field=field_name,
            expected=f"One of: {', '.join(choices)}",
            received=value
        )
    
    return value


def validate_boolean_value(value: str, field_name: str = "boolean option") -> bool:
    """
    Converts a string argument into a boolean value with flexible input formats.

    :param value: str - A string representation of a boolean.
    :param field_name: str - Name of the field being validated.
    :return: bool - The boolean value corresponding to the input.
    :raises ValidationError: If the input is not a valid boolean representation.
    """
    normalized = value.lower().strip()
    
    if normalized in ("0", "false", "no", "off"):
        return False
    elif normalized in ("1", "true", "yes", "on"):
        return True
    else:
        raise ValidationError(
            f"Invalid boolean value for '{field_name}'",
            field=field_name,
            expected="0/1, true/false, yes/no, on/off",
            received=value,
            example="1 or true"
        )
