import argparse
import ast
import sys
import tokenize
from enum import Enum

from docstring_parser import Docstring, DocstringStyle, parse
from docstring_parser.common import ParseError

CHECK_NONE = "noqa_doc"  # Used to ignore checking for docstrings


class DocstringError(Enum):
    """Enum for docstring errors."""

    INVALID_RE_ST = "Docstring is not valid reST in function {}."
    NO_DOCSTRING = "No docstring found in function {}."
    NO_RETURN = "No return docstring found in function {}."
    PARAMS_MISMATCH = "Docstring params do not match function params in function {}."
    PARAMS_MISSING = "Docstring params are missing in function {}."


def _get_docstring_error_message(error_type: DocstringError, function_name: str) -> str:
    """Get error message for a given error type and node.

    :param error_type: Type of docstring error.
    :param function_name: Name of the function.
    :return: Error message.
    """
    return error_type.value.format(function_name)


def main() -> None:
    """Main function for checking docstrings."""
    args = _get_parsed_args()

    return_value = 0
    for file_path in args.file_paths:
        docstring_errors = check_docstrings(
            file_path,
            args.strict or args.disallow_no_docstring,
            args.strict or args.disallow_no_params,
            args.strict or args.disallow_no_return,
        )
        if docstring_errors:
            for docstring_error, line_number in docstring_errors:
                print(f"{file_path}:{line_number}: {docstring_error}")  # noqa: T201
            return_value = 1

    sys.exit(return_value)


def _get_parsed_args() -> argparse.Namespace:
    """Parse command line arguments.

    :return: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Argparse for reST docstring checking.\n\n"
            "Ignore checking for docstrings by adding a comment `# noqa_doc` "
            "one the first line of the of function header."
        ),
    )

    parser.add_argument(
        "file_paths",
        nargs="*",
        help="List of paths to files to check docstrings for",
    )

    arguments = [
        (
            "--disallow-no-docstring",
            "Forces all functions and methods to have docstrings",
        ),
        (
            "--disallow-no-params",
            "Forces all functions to provide all function parameters",
        ),
        (
            "--disallow-no-return",
            "Forces all functions to provide return type if it is not equal to None",
        ),
        (
            "--strict",
            "Forces all functions and methods to have docstrings, "
            "provide all function parameters and return type if it is not None",
        ),
    ]

    for argument, help_text in arguments:
        parser.add_argument(argument, action="store_true", help=help_text)

    return parser.parse_args()


def check_docstrings(
    file_path: str,
    disallow_no_docstring: bool = False,
    disallow_no_params: bool = False,
    disallow_no_return: bool = False,
) -> list[tuple[str, int]]:
    """Check docstrings for a given file.

    :param file_path: Absolute path to file to check docstrings for.
    :param disallow_no_docstring: If True, forces all functions and methods to
    have docstrings.
    :param disallow_no_params: If True, forces all functions to provide all
    function parameters.
    :param disallow_no_return: If True, forces all functions to provide return
    type if it is not equal to None.
    :return: List of errors found in docstrings structured as
    (docstring error, line number).
    """
    module, file_comments = _parse_module_and_extract_comments(file_path)

    docstring_errors = []
    for node in module.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if _ignore_this_function(file_comments, node):
            continue

        docstring_node = ast.get_docstring(node)

        if not docstring_node:
            if disallow_no_docstring:
                docstring_errors.append(
                    (
                        _get_docstring_error_message(
                            DocstringError.NO_DOCSTRING,
                            node.name,
                        ),
                        node.lineno,
                    ),
                )
            continue

        try:
            docstring = parse(docstring_node, DocstringStyle.REST)
        except ParseError:
            docstring_errors.append(
                (
                    _get_docstring_error_message(
                        DocstringError.INVALID_RE_ST,
                        node.name,
                    ),
                    node.lineno,
                ),
            )
            continue

        function_params = {param.arg for param in node.args.args}
        docstring_params = {param.arg_name for param in docstring.params}
        is_at_least_one_undocumented_param = (
            len(function_params) > 0 and len(docstring_params) == 0
        )
        docstring_errors = _check_docstring_params_missing(
            disallow_no_params,
            docstring_errors,
            is_at_least_one_undocumented_param,
            node,
        )
        docstring_errors = _check_docstring_function_params_mismatch(
            docstring_errors,
            docstring_params,
            function_params,
            node,
        )
        docstring_errors = _check_missing_docstring_return(
            disallow_no_return,
            docstring,
            docstring_errors,
            node,
        )

    return docstring_errors


def _check_docstring_params_missing(
    disallow_no_params: bool,
    docstring_errors: list[tuple[str, int]],
    is_at_least_one_undocumented_param: bool,
    node: ast.FunctionDef,
) -> list[tuple[str, int]]:
    """Check if docstring params are missing.

    :param disallow_no_params: If True, forces all functions to provide all
    function parameters.
    :param docstring_errors: List of errors found in docstrings structured
    as (docstring error, line number).
    :param is_at_least_one_undocumented_param: True if there is at least
    one undocumented param, False otherwise.
    :param node: AST node of the function.
    :return: Updated list of errors found in docstrings structured as
    (docstring error, line number).
    """
    if disallow_no_params and is_at_least_one_undocumented_param:
        docstring_errors.append(
            (
                _get_docstring_error_message(DocstringError.PARAMS_MISSING, node.name),
                node.lineno,
            ),
        )
    return docstring_errors


def _check_docstring_function_params_mismatch(
    docstring_errors: list[tuple[str, int]],
    docstring_params: set[str],
    function_params: set[str],
    node: ast.FunctionDef,
) -> list[tuple[str, int]]:
    """Check if docstring function params mismatch.

    :param docstring_errors: List of errors found in docstrings
    structured as (docstring error, line number).
    :param docstring_params: Set of docstring params.
    :param function_params: Set of function params.
    :param node: AST node of the function.
    :return: Updated list of errors found in docstrings structured
    as (docstring error, line number).
    """
    is_param_mismatch = function_params != docstring_params
    if docstring_params and is_param_mismatch:
        docstring_errors.append(
            (
                _get_docstring_error_message(DocstringError.PARAMS_MISMATCH, node.name),
                node.lineno,
            ),
        )
    return docstring_errors


def _check_missing_docstring_return(
    disallow_no_return: bool,
    docstring: Docstring,
    docstring_errors: list[tuple[str, int]],
    node: ast.FunctionDef,
) -> list[tuple[str, int]]:
    """Check if docstring return is missing.

    :param disallow_no_return: If True, forces all functions to provide return
    type if it is not equal to None.
    :param docstring: Docstring object.
    :param docstring_errors: List of errors found in docstrings structured as
    (docstring error, line number).
    :param node: AST node of the function.
    :return: Updated list of errors found in docstrings structured as
    (docstring error, line number).
    """
    is_return_type_none = _is_function_return_type_none(node)
    docstring_params_or_raises_exists = docstring.params or docstring.raises
    is_docstring_return_missing = (
        not is_return_type_none
        and not docstring.returns
        and (docstring_params_or_raises_exists or disallow_no_return)
    )
    if is_docstring_return_missing:
        docstring_errors.append(
            (
                _get_docstring_error_message(DocstringError.NO_RETURN, node.name),
                node.lineno,
            ),
        )
    return docstring_errors


def _is_function_return_type_none(node: ast.FunctionDef) -> bool:
    """Check if function return type is None.

    :param node: AST node of the function.
    :return: True if function return type is None, False otherwise.
    """
    return not node.returns or (
        isinstance(node.returns, ast.Constant) and str(node.returns.kind) == "None"
    )


def _ignore_this_function(
    file_comments: list[tokenize.TokenInfo],
    node: ast.FunctionDef,
) -> bool:
    """Check if this function should be ignored.

    The function should be ignored if there is a comment on the first line
    of the function header containing the string 'CHECK_NONE' (noqa_doc).

    :param file_comments: List of comments in the file.
    :param node: AST node of the function.
    :return: True if this function should be ignored, False otherwise.
    """
    comments_on_this_line = [
        tokeninfo.string
        for tokeninfo in file_comments
        if tokeninfo.end[0] == node.lineno
    ]
    return any(CHECK_NONE in comment for comment in comments_on_this_line)


def _parse_module_and_extract_comments(
    file_path: str,
) -> tuple[ast.Module, list[tokenize.TokenInfo]]:
    """Parse module and extract comments.

    :param file_path: Absolute path to file to parse.
    :return: Tuple of parsed module and list of comments.
    """
    file_comments = []
    with open(file_path) as file:
        module = ast.parse(file.read())
        file.seek(0)
        file_comments.extend(
            [
                tokeninfo
                for tokeninfo in tokenize.generate_tokens(file.readline)
                if tokeninfo.type == tokenize.COMMENT
            ],
        )
    return module, file_comments


if __name__ == "__main__":
    main()
