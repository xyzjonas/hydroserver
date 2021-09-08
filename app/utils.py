import logging
import traceback


log = logging.getLogger(__name__)


def parse_id_as_int(string_or_int):
    if type(string_or_int) is int:
        return string_or_int
    elif type(string_or_int) is str:
        try:
            return int(string_or_int)
        except Exception:
            traceback.print_exc()
    log.error("Supplied id value must be 'str' or 'int'")
    return None
