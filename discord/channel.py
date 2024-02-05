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

from abc import ABC, abstractmethod
from enum import IntEnum
from dataclasses import dataclass

from .user import User
from enum import IntEnum, auto


class ChannelType(IntEnum):
    GUILD_TEXT = 0
    DM = auto()
    GUILD_VOICE = auto()
    GROUP_DM = auto()
    GUILD_CATEGORY = auto()
    GUILD_ANNOUNCEMENT = auto()
    ANNOUNCEMENT_THREAD = 10
    PUBLIC_THREAD = auto()
    PRIVATE_THREAD = auto()
    GUILD_STAGE_VOICE = auto()
    GUILD_DIRECTORY = auto()
    GUILD_FORUM = auto()
    GUILD_MEDIA = auto()


class IChannel(ABC):

    @abstractmethod
    def _update(self, data):
        ...


@dataclass
class Channel(IChannel):

    id: int
    type: ChannelType
    flags: int

    def __init__(self, state, data):
        self._state = state
        self._update(data)

    def _update(self, data):
        self.id = int(data['id'])
        self.type = ChannelType(data['type'])
        self.flags = int(data['flags'])


@dataclass
class PrivateChannel(IChannel):
    id: int
    type: ChannelType
    flags: int
    recipients: [User]

    def __init__(self, me, channel, data):
        self._state = channel._state
        self.id = channel.id
        self.type = channel.type
        self.flags = channel.flags
        self._update(data)

    def _update(self, data):

        if 'recipients' in data.keys():
            self.recipients = [
                User(
                    state=self._state,
                    data=recipient
                )
                for recipient in data['recipients']
            ]

            return None

        self.recipients = self._gather_recipients(data['recipient_ids'])

    def _gather_recipients(self, recipient_ids):
        """Try and find the ids in the client state"""
        recipients = []

        for recipient_id in recipient_ids:
            recipient_id = int(recipient_id)
            recipients.append(self._state._users[recipient_id])

        return recipients

    def __str__(self):
        return 'Direct message with: {self.recipients[0]}'.format(self=self)


@dataclass
class GroupChannel(IChannel):
    id: int
    type: ChannelType
    flags: int
    name: str
    icon: str
    recipients: [User]

    def __init__(self, channel, data):
        self._state = channel._state
        self.id = channel.id
        self.type = channel.type
        self.flags = channel.flags
        self.recipients = channel.recipients
        self._update(data)

    def _update(self, data):
        self.name = data.get('name')
        self.icon = data.get('icon')

    def _get_channel_name(self):
        if self.name is not None:
            return 'GroupChannel({}'.format(self.name)

        recipient_names = [str(recipient) for recipient in self.recipients]
        return 'GroupChannel({})'.format(', '.join(recipient_names))

    def __str__(self):
        return self._get_channel_name()


@dataclass
class GuildTextChannel(IChannel):
    id: int
    type: ChannelType
    flags: int
    position: int
    name: str
    topic: str = None

    def __init__(self, channel, data):
        self._state = channel
        self.id = channel.id
        self.type = channel.type
        self.flags = channel.flags
        self._update(data)

    def _update(self, data):
        self.name = data['name']
        self.topic = data.get('topic')
        self.position = int(data['position'])


def channel_factory(state, data):
    channel = Channel(state=state, data=data)

    if channel.type is ChannelType.DM:
        return PrivateChannel(me=state._user, channel=channel, data=data)

    if channel.type is ChannelType.GROUP_DM:
        channel = PrivateChannel(me=state._user, channel=channel, data=data)
        return GroupChannel(channel=channel, data=data)

    if channel.type is ChannelType.GUILD_TEXT:
        return GuildTextChannel(channel=channel, data=data)

    # Everything we do not handle, just return the standard channel
    return channel
