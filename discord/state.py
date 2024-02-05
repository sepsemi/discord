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


from .constants import (
    TOKEN_ID_LENGTH,
    HEARTBEAT_TIMEOUT
)

from .device import (
    create_device,
)

from .user import (
    User,
    ClientUser
)

from .guild import Guild
from .channel import channel_factory

from .message import (
    PartialMessage,
    message_factory,

)

from copy import copy


class ConnectionState:

    def __init__(self, loop, token, dispatch, http):
        self.loop = loop
        self.token = token
        self.http = http
        self.dispatch = dispatch
        self.id = token[:TOKEN_ID_LENGTH]
        self.device = self._get_device()
        self.heartbeat_timeout = HEARTBEAT_TIMEOUT

        self.parsers = self._initialize_parsers()
        self.clear()

    def _initialize_parsers(self):
        parsers = {}

        for attr in dir(self):
            if not attr.startswith('parse_'):
                continue

            func = getattr(self, attr)
            parsers[attr[6:].upper()] = func

        return parsers

    def _get_device(self):
        return create_device()

    def clear(self):
        self._ready = False
        self._messages = {}
        self._channels = {}
        self._guilds = {}
        self._roles = {}
        self._users = {}
        self._user = None

    def _create_client_user(self, data):
        """Creates a ClientUser"""

        user = User(state=self, data=data)

        # Add ourselfs to the collection
        self._users[user.id] = user

        return ClientUser(user=user, data=data)

    def _add_guild_from_data(self, data):
        """Creates and adds the Guild to the state processing everything"""

        guild = Guild(state=self, data=data)
        self._guilds[guild.id] = guild

    def _create_message(self, data):
        channel, guild = self._get_guild_channel(data)

        if channel is None:
            return None

        # Create the message from the channel and or guild
        return message_factory(guild, channel, data)

    def parse_ready(self, data):
        self._user = self._create_client_user(data['user'])

        for user_data in data['users']:
            user = User(state=self, data=user_data)
            self._users[user.id] = user

        for channel_data in data['private_channels']:
            channel = channel_factory(state=self, data=channel_data)
            self._channels[channel.id] = channel

        for guild_data in data['guilds']:
            self._add_guild_from_data(guild_data)

        self._ready = True
        self.dispatch('ready')

    def parse_channel_create(self, data):
        channel = channel_factory(state=self, data=data)
        self._channels[channel.id] = channel

        self.dispatch('channel_create', channel)

    def parse_channel_update(self, data):
        channel_id = int(data['id'])

        channel = self._channels[channel_id]
        channel._update(data)

        self.dispatch('channel_update', data)

    def parse_channel_delete(self, data):
        return None

    def _get_guild_channel(self, data):
        """Gets a channel by id or channel and guild by id"""

        channel_id = int(data['channel_id'])
        try:
            channel = self._channels[channel_id]
        except KeyError:
            return (None, None)

        try:
            guild_id = int(data['guild_id'])
            guild = self._guilds[guild_id]
        except KeyError:
            return (channel, None)

        return channel, guild

    def parse_message_create(self, data):

        # Create the message from the channel and or guild
        message = self._create_message(data)

        if message is None:
            return None

        self.dispatch('message', message)
        self._messages[message.id] = message

    def parse_message_update(self, data):
        # Create a partial message because we don't know if it exists

        raw = PartialMessage(data)

        if raw.id not in self._messages.keys():
            return None

        # This is not a message with content
        if 'content' not in data.keys():
            return None

        # Fetch the old message from the cache
        message = self._messages[raw.id]

        # Create a soft copy of the message
        older_message = copy(message)

        # Update the message data

        message._update(data)

        self.dispatch('message_edit', older_message, message)

    def parse_message_delete(self, data):
        # Create a partial message because we don't know if it exists
        raw = PartialMessage(data)

        # Find the message in the current cache
        if raw.id not in self._messages.keys():
            return None

        self.dispatch('message_delete', self._messages[raw.id])
