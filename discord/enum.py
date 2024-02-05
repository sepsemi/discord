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


from enum import (
    auto,
    Enum,
    IntEnum,
)


class EnumerableEnum(Enum):
    @classmethod
    def to_dict(cls):
        """Returns a dictionary representation of the enum."""
        return {e.name: e.value for e in cls}

    @classmethod
    def keys(cls):
        """Returns a list of all the enum keys."""
        return cls._member_names_

    @classmethod
    def values(cls):
        """Returns a list of all the enum values."""
        return list(cls._value2member_map_.keys())

    def __str__(self):
        return str(self.value)


class GatewayOpcode(EnumerableEnum):
    DISPATCH = 0x0
    HEARTBEAT = auto()
    IDENTIFY = auto()
    PRESENCE = auto()
    VOICE_STATE = auto()
    VOICE_PING = auto()
    RESUME = auto()
    RECONNECT = auto()
    REQUEST_MEMBERS = auto()
    INVALIDATE_SESSION = auto()
    HELLO = auto()
    HEARTBEAT_ACK = auto()
    GUILD_SYNC = auto()
    DM_UPDATE = auto()
    LAZY_REQUEST = auto()


class GatewayEvent(str, EnumerableEnum):
    READY = 'READY'
    RESUMED = 'RESUMED'
    SESSIONS_REPLACE = 'SESSIONS_REPLACE'
    READY_SUPPLEMENTAL = 'READY_SUPPLEMENTAL'
    GUILD_MEMBERS_CHUNK = 'GUILD_MEMBERS_CHUNK'
