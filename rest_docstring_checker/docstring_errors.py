from enum import Enum


class DocstringError(Enum):
    """Enum for docstring errors."""

    INVALID_RE_ST = "Docstring is not valid reST in function {}"
    NO_DOCSTRING = "No docstring found in function {}"
    NO_RETURN = "No return docstring found in function {}"
    PARAMS_MISMATCH = "Docstring params do not match function params in function {}"
    PARAMS_MISSING = "Docstring params are missing in function {}"


def get_docstring_error_message(error_type: DocstringError, function_name: str) -> str:
    """Get error message for a given error type and node.

    :param error_type: Type of docstring error.
    :param function_name: Name of the function.
    :return: Error message.
    """
    return error_type.value.format(function_name)
