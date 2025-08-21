import enum

class GlueSprayApplicationState(enum.Enum):
    INITIALIZING = "initializing"
    IDLE = "idle"
    STARTED = "started"