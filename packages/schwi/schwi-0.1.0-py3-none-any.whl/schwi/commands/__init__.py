"""Command registrations for the CLI."""

from .basic import (
    clear,
    commands,
    echo,
    exit,
    help,
    quit,
    resume,
    session,
    sessions,
    sysinfo,
    time,
)
from .chat import say

__all__ = [
    'clear',
    'commands',
    'echo',
    'exit',
    'help',
    'quit',
    'resume',
    'say',
    'session',
    'sessions',
    'sysinfo',
    'time',
]
