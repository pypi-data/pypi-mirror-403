import sys


def get_function_name(parents: int = 0) -> str:
    """Get the name of the calling function."""
    # pylint:disable=protected-access
    return sys._getframe(1 + parents).f_code.co_name
