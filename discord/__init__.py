"""
Copyright (C) [2024] [sepsemi]

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""


import logging

from .client import Client
from .state import ConnectionState

from .channel import *


def logger(level="info"):
    # setup a basic logger

    logger = logging.getLogger(__name__)
    log_formatter = logging.Formatter(
        '[%(levelname)s][%(asctime)s][%(className)s][%(funcName)s][%(clientId)s]: %(message)s'
    )

    """
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    """
    file_handler = logging.FileHandler('etc/discord.log')
    file_handler.setFormatter(log_formatter)

    """
    logger.addHandler(console_handler)
    """
    logger.addHandler(file_handler)
    logger.setLevel(getattr(logging, level.upper()))

    return logger
