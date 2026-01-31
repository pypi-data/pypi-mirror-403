import re

def to_snake_case(s: str) -> str:
    """
    Convert any string into snake_case.
    Handles:
      - camelCase / PascalCase
      - mixed separators (-, space, ., !, etc.)
      - multiple underscores
      - trims leading/trailing separators
    """
    if not isinstance(s, str):
        raise TypeError("Input must be a string")

    # Trim spaces
    s = s.strip()
    if not s:
        return ""

    # Insert underscore between lower/number and upper case letters
    # "helloWorld" -> "hello_World"
    s = re.sub(r'(?<=[0-9a-z])(?=[A-Z])', '_', s)

    # Insert underscore between acronyms and normal words
    # "HTTPResponse" -> "HTTP_Response"
    s = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', '_', s)

    # Replace all non-word chars with underscore
    # \W = anything except letters, digits, underscore
    s = re.sub(r'\W+', '_', s)

    # Replace spaces if any remain
    s = s.replace(" ", "_")

    # Collapse multiple underscores
    s = re.sub(r'_+', '_', s)

    # Remove leading/trailing underscores
    s = s.strip('_')

    return s.lower()
