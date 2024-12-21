"""Models."""

import re
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, StringConstraints, create_model

JSON_SCHEMA_TYPE = Literal["string", "number", "integer", "object", "array", "boolean", "null"]


def create_pydantic_model_from_schema(schema: dict[str, Any], model_name: str = "IDF") -> type[BaseModel]:
    """Dynamically creates a Pydantic model based on a given JSON schema.

    Handles patternProperties nested within the properties dictionary.

    Args:
        schema: JSON Schema dictionary.
        model_name: Name of the Pydantic model.

    Returns:
        Pydantic model class.
    """
    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))

    # Define fields for the Pydantic model
    model_fields = {}

    for field_name, field_schema in properties.items():
        # Check if this field has `patternProperties`
        if "patternProperties" in field_schema:
            pattern_properties = field_schema["patternProperties"]
            pattern, nested_model = create_pydantic_model_for_pattern_properties(
                pattern_properties, model_name=field_name
            )
            model_fields[field_name] = (
                dict[Annotated[str, StringConstraints(pattern=pattern)], nested_model],
                None,
            )
        else:
            # Regular field
            field_type = get_python_type_from_json_schema(field_schema)
            field_default = ...  # Ellipsis indicates a required field
            if field_name not in required_fields:
                field_default = field_schema.get("default", None)
            model_fields[field_name] = (field_type, Field(field_default, description=field_schema.get("note")))

    # rename model_name to make sure it is a valid python attribute name
    model_name = re.sub(r"\W", "_", model_name)

    return create_model(model_name, **model_fields)  # type: ignore[reportUnkownArgumentType]


def create_pydantic_model_for_pattern_properties(
    pattern_properties: dict[str, Any], model_name: str
) -> tuple[str, type[BaseModel]]:
    """Creates a Pydantic model for patternProperties.

    Args:
        pattern_properties: The patternProperties dictionary from the schema.
        model_name: Name of the Pydantic model.
    Returns: Pydantic model class.
    """
    for pattern, pattern_schema in pattern_properties.items():
        field_type = get_python_type_from_json_schema(pattern_schema, model_name=model_name)
        return pattern, field_type
    msg = "No patternProperties found in schema."
    raise ValueError(msg)


def get_python_type_from_json_schema(field_schema: dict[str, Any], model_name: str | None = None) -> Any:
    """Maps JSON Schema types to Python types.

    Handles nested schemas and enums.

    Args:
        field_schema (dict): Schema for a specific field.
        model_name (optional, str): Name of the Pydantic model.

    Return: Python type corresponding to the JSON Schema type.
    """
    if "anyOf" in field_schema:
        return get_python_type_from_any_of(field_schema["anyOf"])

    # Default to string if type is not defined
    json_type: JSON_SCHEMA_TYPE = field_schema.get("type", "string")

    type_mapping = {
        "string": str,
        "number": float,
        "integer": int,
        "boolean": bool,
        "array": list[Any],
        "object": dict[str, Any],
    }

    # Handle enums
    if "enum" in field_schema:
        enum: list[str | int | float] = field_schema["enum"]
        return Literal[tuple(type_mapping.get(json_type, str)(v) for v in enum)]  # type: ignore[reportCallIssue]

    # Handle nested object schemas
    if json_type == "object" and "properties" in field_schema and model_name:
        return create_pydantic_model_from_schema(field_schema, model_name=model_name)

    # Handle arrays with item types
    if json_type == "array" and "items" in field_schema:
        item_type = get_python_type_from_json_schema(field_schema["items"])
        return list[item_type]

    if json_type == "number" or json_type == "integer":
        return Annotated[
            type_mapping.get(json_type, Any),
            Field(
                ...,
                ge=field_schema.get("minimum"),
                le=field_schema.get("maximum"),
                description=field_schema.get("note"),
                json_schema_extra={"units": field_schema.get("units")},
            ),
        ]

    return type_mapping.get(json_type, Any)


def get_python_type_from_any_of(any_of_schema: list[dict[str, Any]]):
    """Parses an 'anyOf' schema and generates a Pydantic Union type."""
    return Union[tuple(get_python_type_from_json_schema(schema) for schema in any_of_schema)]  # noqa: UP007


if __name__ == "__main__":
    import json

    # Sample JSON Schema
    with open("archetypal_core/schemas/Energy+.schema.epJSON") as r:
        json_schema = json.load(r)

    # Create a dynamic Pydantic model
    IDF = create_pydantic_model_from_schema(json_schema, model_name="IDF")

    with open("archetypal_core/schemas/idfantic.json", "w") as f:
        json.dump(IDF.model_json_schema(), f)
