import uuid

__all__ = ["uuid_namegen"]


def uuid_namegen(filename: str) -> str:
    """
    Generates a unique filename by combining a UUID and the original filename.

    Args:
        filename (str): The original filename to be used in the unique name.

    Returns:
        str: The generated unique filename.
    """
    return str(uuid.uuid1()) + "_sep_" + filename
