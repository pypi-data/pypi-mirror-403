# -*- coding: utf-8 -*-
"""
Common enumerations used across the AgentBay SDK.

This module contains enumeration classes that are shared between
synchronous and asynchronous implementations.
"""

from enum import Enum


class SessionStatus(Enum):
    """
    Enumeration of valid session status values.
    
    These status values represent the different states a session can be in
    during its lifecycle in the AgentBay cloud environment.
    """
    RUNNING = "RUNNING"
    PAUSING = "PAUSING"
    PAUSED = "PAUSED"
    RESUMING = "RESUMING"
    DELETING = "DELETING"
    DELETED = "DELETED"
