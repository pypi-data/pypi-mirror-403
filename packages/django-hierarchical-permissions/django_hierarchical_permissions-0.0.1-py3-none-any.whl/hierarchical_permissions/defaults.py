from enum import Enum


class PermissionStrategy(str, Enum):
    OBJECT = "olp"
    MODEL = "regular"
    HARDCODED = "hardcoded"


PERMISSION_TYPE = {
    "FIELD": "field",
    "ALL_FIELDS": "fields",
    "WEEKEND": "isWeekend",
    "OWNER": "owner",
}

PERMISSION_TYPES_LABELS = {
    "WEEKEND": lambda action_value, model_name: f"Can {action_value} {model_name} only when it's weekend",
    "FIELD": lambda action_value, model_name, field: f"Can {action_value} {field} field from {model_name} model",
    "OWNER": lambda action_value, model_name: f"Can {action_value} {model_name} when user is assigned to owner field",
    "ALL_FIELDS": lambda action_value, model_name: f"Can {action_value} all fields in {model_name}",
}

PERMISSION_DIVIDER_BY_STRATEGY = {
    PermissionStrategy.OBJECT: [
        "OWNER",
    ],
    PermissionStrategy.MODEL: [
        "FIELD",
        "ALL_FIELDS",
    ],
    PermissionStrategy.HARDCODED: [
        "WEEKEND",
    ],
}

ACTION = {
    "ADD": "add",
    "CHANGE": "change",
    "VIEW": "view",
    "DELETE": "delete",
}

ORGANIZATIONAL_UNITS_TYPES = (
    ("ROOT", "Root"),
    ("GROUP", "Group"),
)
