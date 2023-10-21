import argparse
import sys

from rest_docstring_checker.docstring_checker import check_docstrings


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


if __name__ == "__main__":
    main()
