import enum


class Level(enum.Enum):
    Trace = 0
    """Most detailed logging level, for tracing program execution"""

    Debug = 1
    """Debugging information, useful during development"""

    Info = 2
    """General informational messages about program operation"""

    Warning = 3
    """Warning messages for potentially harmful situations"""

    Error = 4
    """Error messages for serious problems"""

    Critical = 5
    """Critical errors that may lead to program termination"""

    Off = 6
    """Disables all logging"""

def set_level(lvl: Level) -> None:
    """
    Sets the global logging level. Messages with severity levels lower than this level will not be logged.
    """
