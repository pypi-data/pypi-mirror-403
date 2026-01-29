from argparse import ArgumentError
from django.core.exceptions import ImproperlyConfigured

from django.conf import settings
from enum import Enum
from types import MappingProxyType
from . import defaults
from .defaults import PermissionStrategy
import copy

SETTINGS_KEY = "HIERARCHICAL_PERMISSIONS_SETTINGS"


def get_user_setting(key, default):
    user_settings = getattr(settings, SETTINGS_KEY, {})
    return user_settings.get(key, default)


def _create_enum(name, base_data, user_data):
    combined_data = base_data.copy()
    if user_data:
        combined_data.update(user_data)
    return Enum(name, combined_data, type=str)


def _merge_dicts(base, user):
    merged = base.copy()
    if user:
        merged.update(user)
    return MappingProxyType(merged)


def _merge_lists(base, user):
    merged = list(base)
    if user:
        merged.extend(user)
    return tuple(merged)


def _init_permission_subtypes():
    user_subtypes_with_labels = get_user_setting("EXTRA_PERMISSION_SUBTYPES", {})
    permission_levels = [e for e in PermissionStrategy]
    if not all(
        permission_level.value in user_subtypes_with_labels.keys()
        for permission_level in permission_levels
    ):
        raise ImproperlyConfigured(
            f"Invalid keys in HIERARCHICAL_PERMISSIONS_SETTINGS['EXTRA_PERMISSION_SUBTYPES']: "
            f"{', '.join(permission_levels)}. "
            f"Allowed values are: {', '.join(PermissionStrategy.__members__.keys())}"
        )
    new_permission_subtypes = []
    new_subtypes_labels = {}
    new_permission_divider_by_types = {}
    try:
        start_of_permission_subtype_divided_by_level = 0
        for permission_level in permission_levels:
            permission_subtypes = user_subtypes_with_labels.get(
                permission_level.value, []
            )
            for permission_subtype in permission_subtypes:
                if not isinstance(permission_subtype, tuple) or not (
                    2 <= len(permission_subtype) <= 3
                ):
                    raise ImproperlyConfigured
                new_permission_subtypes.append(
                    (permission_subtype[0], permission_subtype[1])
                )
                if len(permission_subtype) != 3:
                    continue
                if not callable(permission_subtype[2]):
                    raise ImproperlyConfigured
                new_subtypes_labels[permission_subtype[0]] = permission_subtype[2]
            new_permission_divider_by_types[permission_level] = new_permission_subtypes[
                start_of_permission_subtype_divided_by_level:
            ]
            start_of_permission_subtype_divided_by_level = len(new_permission_subtypes)
    except ImproperlyConfigured:
        raise ImproperlyConfigured(
            "Invalid EXTRA_PERMISSION_SUBTYPES configuration.\n\n"
            "Expected structure:\n"
            "EXTRA_PERMISSION_SUBTYPES = {\n"
            "    'value of PermissionLevel ': [\n"
            "        (\n"
            "            'PermissionSubType enum name',        # str\n"
            "            'PermissionSubType codename',       # str\n"
            "            callable(optional),       # (action, model,optional(field)) -> str\n"
            "        ),\n"
            "    ],\n"
            "}\n\n"
            "Each value must be a list of tuples with 2 or 3 elements."
        )
    return (
        new_permission_subtypes,
        new_subtypes_labels,
        new_permission_divider_by_types,
    )


def get_organizational_unit_types() -> list[tuple[str, str]]:
    _user_org_types = get_user_setting("EXTRA_ORG_UNIT_TYPES", [])
    final_choices = [
        defaults.ORGANIZATIONAL_UNITS_TYPES[0],
        *_user_org_types,
        *defaults.ORGANIZATIONAL_UNITS_TYPES[1:],
    ]
    return final_choices


def _get_permission_types_labels():
    from hierarchical_permissions.defaults import (
        PERMISSION_TYPES_LABELS as DEFAULT_PERMISSION_TYPES_LABELS,
    )

    final_labels = {}
    default_subtypes_labels = {
        key: handler for key, handler in DEFAULT_PERMISSION_TYPES_LABELS.items()
    }
    for key_name, handler in (default_subtypes_labels | extra_subtypes_labels).items():
        try:
            enum_member = getattr(PermissionType, key_name)
            final_labels[enum_member] = handler
        except AttributeError:
            pass
    return final_labels


def _get_permission_divider_by_strategy():
    _user_dividers = get_user_setting("EXTRA_DIVIDERS", {})
    _combined_dividers = copy.deepcopy(defaults.PERMISSION_DIVIDER_BY_STRATEGY)

    for key, val_list in extra_permission_divider_by_types.items():
        _combined_dividers[key].extend(val[0] for val in val_list)

    final_dividers = {}
    for category, members in _combined_dividers.items():
        enum_members = []
        for member_name in members:
            if hasattr(PermissionType, member_name):
                enum_members.append(getattr(PermissionType, member_name))
        final_dividers[category] = tuple(enum_members)
    return final_dividers


extra_permission_subtypes, extra_subtypes_labels, extra_permission_divider_by_types = (
    _init_permission_subtypes()
)
# PermissionType declaration
PermissionType = _create_enum(
    "PermissionType", defaults.PERMISSION_TYPE, extra_permission_subtypes
)

_user_actions = get_user_setting("EXTRA_ACTIONS", {})
# Action declaration
Action = _create_enum("Action", defaults.ACTION, _user_actions)

# PERMISSION_TYPES_LABELS declaration
PERMISSION_TYPES_LABELS = MappingProxyType(_get_permission_types_labels())

# PERMISSION_DIVIDER_BY_STRATEGY declaration
PERMISSION_DIVIDER_BY_STRATEGY = MappingProxyType(_get_permission_divider_by_strategy())
