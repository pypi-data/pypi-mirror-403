"""This module stores enum classes for consistent use across the library"""

from enum import Enum

class Status(Enum):
    """
    Enum class for the status of an export
    """
    UNSTAGED = 0
    PENDING = 1
    SKIPPED = 2
    PROCESSED = 3
    UNCHANGED = 13
    UNCHANGED_INCOMPLETE = 14
    CHANGED = 15
    NEW = 16
    DETAILS_CHANGED = 17
    DETAILS_CHANGED_INCOMPLETE = 18

class Action(Enum):
    """
    Enum class for the action to be taken on an export
    """
    CONTINUE = 10
    SKIP = 11
    DELAY = 12
