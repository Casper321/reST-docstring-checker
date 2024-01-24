import pytest

from rest_docstring_checker.docstring_checker import check_docstrings
from rest_docstring_checker.docstring_errors import (
    DocstringError,
    get_docstring_error_message,
)

TEST_FILE_NAME = "test.py"
TEST_FILE_DIR = "data"
TEST_FUNCTION_NAME = "test_fn"


@pytest.fixture
def test_file_path(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Create a test file with a function with a docstring.

    :param tmp_path_factory: Pytest fixture.
    :return: Path to the temporary test file.
    """
    test_file_path = tmp_path_factory.mktemp(TEST_FILE_DIR) / TEST_FILE_NAME

    with open(test_file_path, "w") as test_file:
        content = '''
def test_fn(x: int, y: int) -> int:
    """Test function.

    :param x: First integer.
    :param y: Second integer.
    :return: Sum of integers.
    """
    return x + y
'''
        # Remove the first blank line
        test_file.write(content.lstrip("\n"))

    return str(test_file_path)


def test_check_docstrings_no_disallow(test_file_path: str) -> None:
    """
    Test that no errors are raised when all disallow parameters are set to False.

    :param test_file_path: Path to the test file fixture.
    """
    errors = check_docstrings(test_file_path)
    assert len(errors) == 0


def test_check_docstrings_disallow_no_docstring(test_file_path: str) -> None:
    """Test that no errors are raised when disallow_no_docstring is set to True.

    :param test_file_path: Path to the test file fixture.
    """
    errors = check_docstrings(test_file_path, disallow_no_docstring=True)
    assert len(errors) == 0


def test_check_docstrings_disallow_no_params(test_file_path: str) -> None:
    """Test that no errors are raised when disallow_no_params is set to True.

    :param test_file_path: Path to the test file fixture.
    """
    errors = check_docstrings(test_file_path, disallow_no_params=True)
    assert len(errors) == 0


def test_check_docstrings_disallow_no_return(test_file_path: str) -> None:
    """Test that no errors are raised when disallow_no_return is set to True.

    :param test_file_path: Path to the test file fixture.
    """
    errors = check_docstrings(test_file_path, disallow_no_return=True)
    assert len(errors) == 0


def test_check_docstrings_params_mismatch(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    test_file_path = tmp_path_factory.mktemp(TEST_FILE_DIR) / TEST_FILE_NAME
    with open(test_file_path, "w") as test_file:
        test_file.write(
            '''
def test_fn(x: int, y: int) -> int:
    """Test function.

    :param x: First integer.
    :return: Sum of integers.
    """
    return x + y
        ''',
        )
    errors = check_docstrings(str(test_file_path))
    assert len(errors) > 0
    assert (
        get_docstring_error_message(DocstringError.PARAMS_MISSING, TEST_FUNCTION_NAME)
        == errors[0][0]
    )


def test_check_docstrings_returns_mismatch(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    test_file_path = tmp_path_factory.mktemp(TEST_FILE_DIR) / TEST_FILE_NAME
    with open(test_file_path, "w") as test_file:
        test_file.write(
            '''
def test_fn(x: int, y: int) -> int:
    """Test function.

    :param x: First integer.
    :param y: Second integer.
    """
    return x + y
        ''',
        )
    errors = check_docstrings(str(test_file_path))
    assert len(errors) > 0
    assert (
        get_docstring_error_message(DocstringError.NO_RETURN, TEST_FUNCTION_NAME)
        == errors[0][0]
    )


def test_check_docstrings_variable_length_argument(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    test_file_path = tmp_path_factory.mktemp(TEST_FILE_DIR) / TEST_FILE_NAME
    with open(test_file_path, "w") as test_file:
        test_file.write(
            '''
def test_fn(x: int, y: int, *args, **kwargs) -> int:
    """Test function.

    :param x: First integer.
    :param y: Second integer.
    :param *args: Variable length argument.
    :param **kwargs: Variable length argument.
    :return: Sum of integers.
    """
    return x + y
        ''',
        )
    errors = check_docstrings(str(test_file_path))
    assert len(errors) == 0


def test_check_docstrings_variable_length_argument_missing_args(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    test_file_path = tmp_path_factory.mktemp(TEST_FILE_DIR) / TEST_FILE_NAME
    with open(test_file_path, "w") as test_file:
        test_file.write(
            '''
def test_fn(x: int, y: int, *args, **kwargs) -> int:
    """Test function.

    :param x: First integer.
    :param y: Second integer.
    :param **kwargs: Variable length argument.
    :return: Sum of integers.
    """
    return x + y
        ''',
        )
    errors = check_docstrings(str(test_file_path))
    assert len(errors) > 0
    assert (
        get_docstring_error_message(DocstringError.PARAMS_MISSING, TEST_FUNCTION_NAME)
        == errors[0][0]
    )


def test_check_docstrings_variable_length_argument_redundant_args(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    test_file_path = tmp_path_factory.mktemp(TEST_FILE_DIR) / TEST_FILE_NAME
    with open(test_file_path, "w") as test_file:
        test_file.write(
            '''
def test_fn(x: int, y: int, **kwargs) -> int:
    """Test function.

    :param x: First integer.
    :param y: Second integer.
    :param *args: Variable length argument.
    :param **kwargs: Variable length argument.
    :return: Sum of integers.
    """
    return x + y
        ''',
        )
    errors = check_docstrings(str(test_file_path))
    assert len(errors) == 1
    assert (
        get_docstring_error_message(DocstringError.PARAMS_MISMATCH, TEST_FUNCTION_NAME)
        == errors[0][0]
    )


def test_check_docstrings_variable_length_argument_kwarg_only(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    test_file_path = tmp_path_factory.mktemp(TEST_FILE_DIR) / TEST_FILE_NAME
    with open(test_file_path, "w") as test_file:
        test_file.write(
            '''
def test_fn(x: int, y: int, **kwargs) -> int:
    """Test function.

    :param x: First integer.
    :param y: Second integer.
    :param kwargs: Variable length argument.
    :return: Sum of integers.
    """
    return x + y
        ''',
        )
    errors = check_docstrings(str(test_file_path))
    assert len(errors) == 0


def test_check_docstrings_variable_length_argument_missing_kwargs(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    test_file_path = tmp_path_factory.mktemp(TEST_FILE_DIR) / TEST_FILE_NAME
    with open(test_file_path, "w") as test_file:
        test_file.write(
            '''
def test_fn(x: int, y: int, **kwargs) -> int:
    """Test function.

    :param x: First integer.
    :param y: Second integer.
    :return: Sum of integers.
    """
    return x + y
        ''',
        )
    errors = check_docstrings(str(test_file_path))
    assert len(errors) > 0
    assert (
        get_docstring_error_message(DocstringError.PARAMS_MISSING, TEST_FUNCTION_NAME)
        == errors[0][0]
    )


def test_check_docstrings_variable_length_argument_redundant_kwargs(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    test_file_path = tmp_path_factory.mktemp(TEST_FILE_DIR) / TEST_FILE_NAME
    with open(test_file_path, "w") as test_file:
        test_file.write(
            '''
def test_fn(x: int, y: int) -> int:
    """Test function.

    :param x: First integer.
    :param y: Second integer.
    :param kwargs: Variable length argument.
    :return: Sum of integers.
    """
    return x + y
        ''',
        )
    errors = check_docstrings(str(test_file_path))
    assert len(errors) > 0
    assert (
        get_docstring_error_message(DocstringError.PARAMS_MISMATCH, TEST_FUNCTION_NAME)
        == errors[0][0]
    )


def test_check_docstrings_async_valid(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    test_file_path = tmp_path_factory.mktemp(TEST_FILE_DIR) / TEST_FILE_NAME
    with open(test_file_path, "w") as test_file:
        test_file.write(
            '''
async def test_fn(x: int, y: int) -> int:
    """Test function.

    :param x: First integer.
    :param y: Second integer.
    :return: Sum of integers.
    """
    return x + y
        ''',
        )
    errors = check_docstrings(str(test_file_path))
    assert len(errors) == 0


def test_check_docstrings_async_invalid(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    test_file_path = tmp_path_factory.mktemp(TEST_FILE_DIR) / TEST_FILE_NAME
    with open(test_file_path, "w") as test_file:
        test_file.write(
            '''
async def test_fn(x: int, y: int) -> int:
    """Test function.

    :param x: First integer.
    :return: Sum of integers.
    """
    return x + y
        ''',
        )
    errors = check_docstrings(str(test_file_path))
    assert len(errors) > 0
