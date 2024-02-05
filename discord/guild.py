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


from typing import Dict
from dataclasses import dataclass

from .channel import channel_factory


@dataclass
class Role:
    id: int
    name: str
    hoist: bool
    version: int
    position: int
    permissions: int
    mentionable: bool

    def __init__(self, data):
        self.id = int(data['id'])
        self.name = data['name']
        self.hoist = data['hoist']
        self.version = data['version']
        self.position = data['position']
        self.mentionable = data['mentionable']
        self.permissions = int(data['permissions'])

    def __str__(self):
        return self.name


@dataclass
class Guild:
    id: int
    name: str
    icon: str
    banner: str
    roles: Dict['id', Role]
    channels: Dict['id', channel_factory]

    def __init__(self, state, data):
        self._state = state
        self._update(data)

    def _update(self, data):
        self.id = int(data['id'])
        self.name = data['name']
        self.icon = data['icon']
        self.banner = data['banner']

        # Add all the roles
        self.roles = self._add_roles(data['roles'])

        # Create and add all the relevant channels
        self.channels = self._add_channels(data['channels'])

    def _add_roles(self, roles):
        return {role['id']: self._add_role_from(role) for role in roles}

    def _add_channels(self, channels):
        return {channel['id']: self._add_channel_from_data(channel) for channel in channels}

    def _add_role_from(self, data):
        role = Role(data)
        self._state._roles[role.id] = role

        return role

    def _add_channel_from_data(self, data):
        channel = channel_factory(
            state=self._state,
            data=data
        )

        # Add the channel to the state
        self._state._channels[channel.id] = channel
        return channel
