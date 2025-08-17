"""
Description:
    This module defines all constant values used for API request handling,
    including request types, actions, resources, and standard response statuses.

    These constants are shared across the system to ensure consistency when
    performing API operations or interpreting requests/responses.

Usage:
    Import this module wherever API requests or responses are handled to avoid
    hardcoding string literals and to centralize definitions.
"""

# # === REQUEST TYPES ===
# REQUEST_TYPE_POST = "POST"               # For POST requests (e.g., data submission)
# REQUEST_TYPE_GET = "GET"                 # For GET requests (e.g., retrieve configuration)
# REQUEST_TYPE_EXECUTE = "EXECUTE"         # For EXECUTE requests (e.g., actions to perform)

# === ACTIONS ===
# ACTION_START = "start"                           # Start the glue dispensing operation
# ACTION_STOP = "stop"                             # Stop the operation
                           # Send robot to home position
# ACTION_RESTART = "restart"                       # Restart operation/system

ACTION_CALIBRATE_PICKUP_AREA = "calib pickup area"  # Calibrate pickup area using camera

# SETTINGS_GET = "settings/get"              # Retrieve current system settings
# SETTINGS_SET = "settings/set"              # Apply new settings to the system

# === CAMERA ACTIONS ===
# CAMERA_ACTION_GET_LATEST_FRAME = "camera/getLatestFrame"  # Fetch the latest frame from the camera
# CAMERA_ACTION_RAW_MODE_ON = "camera/rawModeOn"            # Enable raw image mode
# CAMERA_ACTION_RAW_MODE_OFF = "camera/rawModeOff"          # Disable raw image mode

# === ROBOT ACTIONS ===
# REQUEST_ACTION_CURRENT_POSITION = "currentPosition"  # Get robot's current position
           # Save a robot point/position


# Camera resource group
# REQUEST_RESOURCE_GLUE_NOZZLE = "glueNozzle"       # Glue nozzle system resource
# REQUEST_RESOURCE_WORKPIECE = "workpieces"          # Workpiece resource (e.g., spray pattern data)

# === NEW REQUESTS ===
TEST_RUN = "test_run"

# === RESPONSE STATUSES ===
RESPONSE_STATUS_SUCCESS = "success"               # Operation completed successfully
RESPONSE_STATUS_ERROR = "error"                   # Operation failed with an error
RESPONSE_STATUS_WARNING = "warning"               # Operation succeeded with a warning



# === REQUEST RESOURCES ===
REQUEST_RESOURCE_ROBOT = "Robot"                  # Robot resource group
REQUEST_RESOURCE_CAMERA = "Camera"
REQUEST_RESOURCE_GLUE = "Glue"                    # Glue dispensing system resource
REQUEST_RESOURCE_SETTINGS = "Settings"
REQUEST_RESOURCE_WORKPIECE = "Workpiece"
REQUEST_RESOURCE_GLUE_NOZZLE = "GlueNozzle"


LOGIN = "login"
QR_LOGIN = "camera/login"
START_CONTOUR_DETECTION = "camera/START_CONTOUR_DETECTION"
STOP_CONTOUR_DETECTION = "camera/STOP_CONTOUR_DETECTION"
START = "start"
WORKPIECE_CREATE = "workpiece/create"
WORKPIECE_SAVE = "workpiece/save"
WORKPIECE_SAVE_DXF = "workpiece/dxf"
WORKPIECE_GET_ALL = "workpiece/getall"


ROBOT_ACTION_JOG_X_MINUS = "robot/jog/X/Minus"
ROBOT_ACTION_JOG_X_PLUS = "robot/jog/X/Plus"
ROBOT_ACTION_JOG_Y_MINUS = "robot/jog/Y/Minus"
ROBOT_ACTION_JOG_Y_PLUS = "robot/jog/Y/Plus"
ROBOT_ACTION_JOG_Z_MINUS = "robot/jog/Z/Minus"
ROBOT_ACTION_JOG_Z_PLUS = "robot/jog/Z/Plus"
ROBOT_MOVE_TO_CALIB_POS = "robot/move/calibPos"     # Move robot to predefined calibration position
ROBOT_MOVE_TO_HOME_POS = "robot/move/home"           # Move robot to predefined home position
ROBOT_MOVE_TO_LOGIN_POS = "robot/move/login"

ROBOT_STOP = "robot/stop"
ROBOT_SAVE_POINT = "robot/savePoint"
ROBOT_CALIBRATE = "robot/calibrate"
ROBOT_CALIBRATE_PICKUP = "robot/calibPickup"

CAMERA_ACTION_GET_LATEST_FRAME = "camera/getLatestFrame"
CAMERA_ACTION_RAW_MODE_ON = "camera/rawModeOn"            # Enable raw image mode
CAMERA_ACTION_RAW_MODE_OFF = "camera/rawModeOff"
CAMERA_ACTION_CALIBRATE = "camera/calibrate"

SETTINGS_ROBOT_GET = "settings/robot/get"
SETTINGS_ROBOT_SET = "settings/robot/set"

SETTINGS_GLUE_GET = "settings/glue/get"
SETTINGS_GLUE_SET = "settings/glue/set"

SETTINGS_CAMERA_GET = "settings/camera/get"
SETTINGS_CAMERA_SET = "settings/camera/set"