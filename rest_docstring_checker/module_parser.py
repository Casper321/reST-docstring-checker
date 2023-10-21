import ast
import tokenize


def parse_module_and_extract_comments(
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
