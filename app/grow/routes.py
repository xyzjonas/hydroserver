import logging

log = logging.getLogger(__name__)


def _get_id(string_or_int):
    if type(string_or_int) is int:
        return string_or_int
    elif type(string_or_int) is str:
        return int(string_or_int)
    else:
        raise ValueError("Supplied id value must be 'str' or 'int'")
