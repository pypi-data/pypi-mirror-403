import sys

LEVEL_DEBUG = 3
LEVEL_INFO = 4
LEVEL_SILENT = 5
LEVEL_ROAR = 6

__LOG_LEVEL__ = LEVEL_INFO


def set_debug_enabled(enabled):
    set_log_level(LEVEL_DEBUG if enabled else LEVEL_INFO)


def set_silent_enabled(enabled):
    set_log_level(LEVEL_SILENT if enabled else LEVEL_INFO)


def set_log_level(level):
    global __LOG_LEVEL__
    __LOG_LEVEL__ = level


def roar(*args):
    if __LOG_LEVEL__ > LEVEL_ROAR:
        return

    print(*args)


def info(*args):
    if __LOG_LEVEL__ > LEVEL_INFO:
        return

    print(*args)


def warn(*args):
    if __LOG_LEVEL__ > LEVEL_INFO:
        return

    print("\033[33m", *args, "\033[0m")


def error(*args):
    if __LOG_LEVEL__ > LEVEL_INFO:
        return

    print("\033[31m", *args, "\033[0m", file=sys.stderr, sep="")


def debug(*args):
    if __LOG_LEVEL__ > LEVEL_DEBUG:
        return

    print(*args)
