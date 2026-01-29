import partial_json_parser as pjp

from pydantic import BaseModel

from ..core.exceptions import MalformedJSON

def parse_fragment(
    json_fragment: str,
    parsing_schema: type[BaseModel]
) -> BaseModel:
    """Tries to fix a JSON fragment string, and parses into a Pydantic model instance, or return the string as-is.

    This function attempts to load a JSON fragment and validate it against a provided Pydantic model schema.
    If the JSON is malformed, or if validation against the schema fails, appropriate exceptions are raised 
    with detailed error messages.

    Args:
        `json_fragment` (`str`): The JSON fragment string to parse.
        `parsing_schema` (`type[BaseModel]`): A Pydantic model class to validate the parsed JSON against.

    Returns:
        `BaseModel`: If a schema is provided, returns an instance of the schema with validated data.

    Raises:
        `MalformedJSON`: If the input string is not valid JSON.
    """
    
    try:
        fixed_json = pjp.loads(json_fragment) 
        return parsing_schema.model_validate(fixed_json)

    except pjp.MalformedJSON:
        raise MalformedJSON(
            f"Model produced invalid JSON or invalid partial JSON fragment.\n" +
            f"Malformed JSON string: {repr(json_fragment)}"
        ) from None
