import ast
import tokenize

from docstring_parser import Docstring, DocstringStyle, parse
from docstring_parser.common import ParseError

from rest_docstring_checker.constants import CHECK_NONE
from rest_docstring_checker.docstring_errors import (
    DocstringError,
    get_docstring_error_message,
)
from rest_docstring_checker.module_parser import parse_module_and_extract_comments


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
    module, file_comments = parse_module_and_extract_comments(file_path)

    docstring_errors = []
    for node in module.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if _ignore_this_function(node, file_comments):
            continue

        docstring_node = ast.get_docstring(node)

        if not docstring_node:
            if disallow_no_docstring:
                docstring_errors.append(
                    (
                        get_docstring_error_message(
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
                    get_docstring_error_message(
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
            node,
            docstring_errors,
            disallow_no_params,
            is_at_least_one_undocumented_param,
        )
        docstring_errors = _check_docstring_function_params_mismatch(
            node,
            docstring_errors,
            docstring_params,
            function_params,
        )
        docstring_errors = _check_missing_docstring_return(
            node,
            docstring_errors,
            disallow_no_return,
            docstring,
        )

    return docstring_errors


def _check_docstring_params_missing(
    node: ast.FunctionDef,
    docstring_errors: list[tuple[str, int]],
    disallow_no_params: bool,
    is_at_least_one_undocumented_param: bool,
) -> list[tuple[str, int]]:
    """Check if docstring params are missing.

    :param node: AST node of the function.
    :param docstring_errors: List of errors found in docstrings structured
    as (docstring error, line number).
    :param disallow_no_params: If True, forces all functions to provide all
    function parameters.
    :param is_at_least_one_undocumented_param: True if there is at least
    one undocumented param, False otherwise.
    :return: Updated list of errors found in docstrings structured as
    (docstring error, line number).
    """
    if disallow_no_params and is_at_least_one_undocumented_param:
        docstring_errors.append(
            (
                get_docstring_error_message(DocstringError.PARAMS_MISSING, node.name),
                node.lineno,
            ),
        )
    return docstring_errors


def _check_docstring_function_params_mismatch(
    node: ast.FunctionDef,
    docstring_errors: list[tuple[str, int]],
    docstring_params: set[str],
    function_params: set[str],
) -> list[tuple[str, int]]:
    """Check if docstring function params mismatch.

    Clean docstring params from variable length arguments such
    as **kwargs and *args first.

    :param node: AST node of the function.
    :param docstring_errors: List of errors found in docstrings
    structured as (docstring error, line number).
    :param docstring_params: Set of docstring params.
    :param function_params: Set of function params.
    :return: Updated list of errors found in docstrings structured
    as (docstring error, line number).
    """
    clean_docstring_params = {
        docstring_param
        for docstring_param in docstring_params
        if not docstring_param.startswith("*")
    }
    is_param_mismatch = function_params != clean_docstring_params
    if docstring_params and is_param_mismatch:
        docstring_errors.append(
            (
                get_docstring_error_message(DocstringError.PARAMS_MISMATCH, node.name),
                node.lineno,
            ),
        )
    return docstring_errors


def _check_missing_docstring_return(
    node: ast.FunctionDef,
    docstring_errors: list[tuple[str, int]],
    disallow_no_return: bool,
    docstring: Docstring,
) -> list[tuple[str, int]]:
    """Check if docstring return is missing.

    :param node: AST node of the function.
    :param docstring_errors: List of errors found in docstrings structured as
    (docstring error, line number).
    :param disallow_no_return: If True, forces all functions to provide return
    type if it is not equal to None.
    :param docstring: Docstring object.
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
                get_docstring_error_message(DocstringError.NO_RETURN, node.name),
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
    node: ast.FunctionDef,
    file_comments: list[tokenize.TokenInfo],
) -> bool:
    """Check if this function should be ignored.

    The function should be ignored if there is a comment on the first line
    of the function header containing the string 'CHECK_NONE' (noqa_doc).

    :param node: AST node of the function.
    :param file_comments: List of comments in the file.
    :return: True if this function should be ignored, False otherwise.
    """
    comments_on_this_line = [
        tokeninfo.string
        for tokeninfo in file_comments
        if tokeninfo.end[0] == node.lineno
    ]
    return any(CHECK_NONE in comment for comment in comments_on_this_line)
