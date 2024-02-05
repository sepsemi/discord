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


from logging import getLogger

from typing import Dict
from dataclasses import dataclass

from .util import to_json
from .enum import GatewayOpcode

_log = getLogger(__name__)

VIEW_CHANNEL = (1 << 10)
SEND_MESSAGES = (1 << 11)
HISTORY = (1 << 16)

# Permissions we want to have to subscribe
COMBO_PERMISSIONS = VIEW_CHANNEL | SEND_MESSAGES


def compute_channel_permissions(guild, channel):
    role_everyone = guild.roles[guild.id]

    # Set the base permissions from @everyone role
    permissions = role_everyone.permissions

    allow, deny = 0, 0
    for overwrite in channel.overwrites.values():
        allow |= overwrite.allow
        deny |= overwrite.deny

    permissions &= ~deny
    permissions |= allow

    return permissions


def create_channel_subscribe_collection(channel_ids, collection):
    """Create a collection of lists that are linked to a channel_id"""

    channels = {}

    for channel_id in channel_ids:
        channels[str(channel_id)] = collection

    return channels


@dataclass
class PermissionOverwrite:
    id: int
    type: int
    deny: int
    allow: int

    def __init__(self, data):
        self.id = int(data['id'])
        self.type = data['type']
        self.deny = int(data['deny'])
        self.allow = int(data['allow'])


@dataclass
class Role:
    id: int
    name: str
    position: int
    permissions: int

    def __init__(self, data):
        self.id = int(data['id'])
        self.name = data['name']
        self.position = data['position']
        self.permissions = int(data['permissions'])


@dataclass
class GuildChannel:

    id: int
    type: int
    name: str
    position: int
    overwrites: Dict['PermissionOverwrite.id', PermissionOverwrite]

    def __init__(self, data):
        self.id = int(data['id'])
        self.type = data['type']
        self.name = data['name']
        self.position = int(data['position'])
        self.overwrites = self._get_overwrites(data['permission_overwrites'])

    def _get_overwrites(self, data):
        return {int(overwrite['id']): PermissionOverwrite(overwrite) for overwrite in data}


@dataclass
class Guild:
    id: int
    name: str
    count: int
    roles: [Role]
    channels: Dict['GuildChannel.id', GuildChannel]

    def __init__(self, data):
        self.id = int(data['id'])
        self.name = data['name']
        self.count = int(data['member_count'])
        self.roles = self._get_roles(data['roles'])
        self.channels = self._get_channels(data['channels'])

    def _get_roles(self, data):
        return {int(role['id']): Role(role) for role in data}

    def _get_channels(self, data):
        return {int(channel['id']): GuildChannel(channel) for channel in data}


class GuildSubscriber:
    STEP_SIZE = 300
    MAX_MEMBERS = 99

    def __init__(self, gateway):
        self.id = gateway.id
        self.loop = gateway.loop
        self.websocket = gateway._websocket

        self.guilds = {}
        self.user_id = None

    def get_payload(self, id):
        """The payload template used to request a subscription"""

        return {
            "op": GatewayOpcode.LAZY_REQUEST.value,
            "d": {
                "guild_id": str(id),
                "typing": True,
                "threads": True,
                "activities": True,
                'members': [],
                'thread_member_lists': [],
            }
        }

    def reguest_members(self, id):
        """Requests the members for this guild"""

        return {
            "op": GatewayOpcode.REQUEST_MEMBERS.value,
            "d": {
                "guild_id": str(id),
                "query": "",
                "limit": 0
            }
        }

    async def guild_members_chunk(self, data):
        """A response to request_members"""

    def register(self, data):
        """Registers a guild to the internal cache"""

        guild = Guild(data)
        self.guilds[guild.id] = guild

        return guild

    async def subscribe_to_channel(self, guild, channel):
        """Subscribes to events from a given channel in that guild"""

        _log.debug(
            'Subscribing to id=%s, name=%s, channel_id=%s, channel_name=%s',
            guild.id,
            guild.name,
            channel.id,
            channel.name,
            extra={
                'className': self.__class__.__name__,
                'clientId': self.id,
            }
        )

        collection = []
        payload = self.get_payload(guild.id)

        # We do not care about guild.count for now, we set a hard limit
        for i in range(0, self.MAX_MEMBERS, self.STEP_SIZE):
            collection.append([i, i + self.STEP_SIZE - 1])

            if i % self.STEP_SIZE == 0:
                payload['channels'] = create_channel_subscribe_collection(
                    [channel.id],
                    collection
                )

                payload = to_json(payload)
                await self.websocket.send(payload)

    async def subscribe(self, guild):
        """Subscribes to the correct and permissive channels in a guild"""

        for id, channel in guild.channels.items():
            # Only get the text channels
            if channel.type != 0:
                continue

            # The permissions calculated based on @everyone and channel overwrites
            permissions = compute_channel_permissions(guild, channel)

            if not (permissions & COMBO_PERMISSIONS) == COMBO_PERMISSIONS:
                continue

            await self.subscribe_to_channel(guild, channel)

    async def process(self, guilds):
        for guild in guilds:
            guild = self.register(guild)

        # Subscribe to the registered guilds
        for id, guild in self.guilds.items():
            await self.subscribe(guild)

# 16381
