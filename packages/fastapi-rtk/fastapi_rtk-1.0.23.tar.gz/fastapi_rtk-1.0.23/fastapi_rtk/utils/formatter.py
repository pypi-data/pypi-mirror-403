import math
import typing

__all__ = ["prettify_dict", "format_file_size"]


def prettify_dict(d: typing.Dict[str, typing.Any], indent: int = 0) -> str:
    """
    Prettify a dictionary to a string.

    Args:
        d (Dict[str, Any]): The dictionary to be prettified.
        indent (int, optional): The number of spaces to indent each level. Defaults to 0.

    Returns:
        str: The prettified dictionary as a string.
    """
    result = ""
    for key, value in d.items():
        result += " " * indent + f"{key}: "
        if isinstance(value, dict):
            result += "\n" + prettify_dict(value, indent + 2)
        else:
            result += f"{value}\n"
    return result


def format_file_size(size_bytes: int):
    """
    Format a file size in bytes to a human-readable string.

    Args:
        size_bytes (int): The file size in bytes.

    Returns:
        str: The formatted file size.
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    if s.is_integer():
        s = int(s)
    return f"{s} {size_name[i]}"
