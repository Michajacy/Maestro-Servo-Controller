"""
Configuration module for Maestro Servo Controller.
Centralizes all constants, default values, and UI settings.
"""

# UI Constants - Geometry & Styling
MAIN_WIN_GEO = "400x500"
SERVO_WIN_W = 250
SERVO_WIN_H = 150
MAIN_WIN_INPUT_AREA_WIDTH = 15
PAD_XS = 2
PAD_S = 5
PAD_M = 10
PAD_L = 15
SLIDER_W = 200
COLOR_SELECTED = "#97B7F8"
COLOR_DEFAULT = "#FFFFFF"

# UI Constants - Texts
TXT_APP_TITLE = "Maestro App"
TXT_GROUP_SETTINGS = "Servo settings"
TXT_GROUP_LIST = "Active servos"
TXT_LBL_NAME = "Name:"
TXT_LBL_STEP = "Jog Step (us):"
TXT_LBL_MIN = "Min Pos:"
TXT_LBL_MAX = "Max Pos:"
TXT_LBL_POS = "Position: {} us"
TXT_BTN_ADD = "+ Add servo"
TXT_BTN_SAVE = "Save Changes"
TXT_BTN_DEL = "X"
TXT_BTN_LEFT = "<-"
TXT_BTN_RIGHT = "->"

#UI Constants - ComboBox
COMBO_W = 10
COMBO_STATE = "readonly"
COMBO_VALUES = ["Mock", "Serial"]
COMBO_TXT = "Hardware Interface:"

# UI Constants - Messages
MSG_WARN_TITLE = "No free channels"
MSG_WARN_TEXT = "All channels occupied."
MSG_INFO_TITLE = "Info"
MSG_INFO_SELECT = "Select a servo from the list first."
MSG_SAVE_TITLE = "Saved"
MSG_SAVE_TEXT = "Configuration for '{}' saved!"
MSG_ERR_VAL_TITLE = "Validation Error"
MSG_ERR_VAL_INT = "Numeric fields cannot be empty and must be valid integers."
MSG_ERR_VAL_STEP = "Jog Step must be strictly greater than 0."
MSG_ERR_VAL_NEG = "Position limits cannot be negative."
MSG_ERR_VAL_MINMAX = "Min Pos must be strictly less than Max Pos."
MSG_ERR_VAL_LARGE = "Max Pos is too large (maximum allowed is 10000 us)."

# Servo Defaults
SERVO_DEF_NAME = "New Servo"
SERVO_DEF_STEP = 50
SERVO_DEF_MIN = 1000
SERVO_DEF_MAX = 2000
SERVO_DEF_POS = 1500

# Hardware & System Constants
MAX_CHANNELS = 24
DEFAULT_COM_PORT = "COM3"
DEFAULT_BAUDRATE = 9600
DEFAULT_HW_MODE = "Mock"
CMD_SET_TRGT = 0x84
