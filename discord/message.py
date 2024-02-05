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


from dataclasses import dataclass

from .user import User
from .guild import Guild
from .channel import channel_factory

from enum import IntEnum, auto


class MessageType(IntEnum):
    DEFAULT = 0
    RECIPIENT_ADD = auto()
    RECIPIENT_REMOVE = auto()
    CALL = auto()
    CHANNEL_NAME_CHANGE = auto()
    CHANNEL_ICON_CHANGE = auto()
    CHANNEL_PINNED_MESSAGE = auto()
    USER_JOIN = auto()
    GUILD_BOOST = auto()
    GUILD_BOOST_TIER_1 = auto()
    GUILD_BOOST_TIER_2 = auto()
    GUILD_BOOST_TIER_3 = auto()
    CHANNEL_FOLLOW_ADD = auto()
    GUILD_DISCOVERY_DISQUALIFIED = auto()
    GUILD_DISCOVERY_REQUALIFIED = auto()
    GUILD_DISCOVERY_GRACE_PERIOD_INITIAL_WARNING = auto()
    GUILD_DISCOVERY_GRACE_PERIOD_FINAL_WARNING = auto()
    THREAD_CREATED = auto()
    REPLY = auto()
    CHAT_INPUT_COMMAND = auto()
    THREAD_STARTER_MESSAGE = auto()
    GUILD_INVITE_REMINDER = auto()
    CONTEXT_MENU_COMMAND = auto()
    AUTO_MODERATION_ACTION = auto()
    ROLE_SUBSCRIPTION_PURCHASE = auto()
    INTERACTION_PREMIUM_UPSELL = auto()
    STAGE_START = auto()
    STAGE_END = auto()
    STAGE_SPEAKER = auto()
    STAGE_TOPIC = auto()
    GUILD_APPLICATION_PREMIUM_SUBSCRIPTION = auto()


class PartialMessage:

    def __init__(self, data):
        self.id = int(data['id'])
        self.channel_id = int(data['channel_id'])


@dataclass
class Message:
    id: int
    type: MessageType
    content: str
    author: User
    guild: Guild
    channel: channel_factory

    def __init__(self, guild, channel, data):
        self._state = channel._state
        self.guild = guild
        self.channel = channel
        self.id = int(data['id'])
        self.type = MessageType(data['type'])
        self.author = self._get_author(data['author'])
        self._update(data)

    def _get_author(self, data):
        return User(state=self._state, data=data)

    def _update(self, data):
        self.content = data['content']


def message_factory(guild, channel, data):
    message = Message(guild=guild, channel=channel, data=data)

    if message.type == MessageType.DEFAULT:
        return message
