"""
.. include:: ../subdocs/main.md
"""

from .main import Bot
from .main import TypingInfo, User, Message, Server, Channel, ctx
from . import enums, types, addons

__all__ = [
    'Bot', # main class
    'TypingInfo', 'User', 'Message', 'Server', 'Channel', 'ctx', # additional classes
    'enums', 'types', 'addons' # submodules
    ]