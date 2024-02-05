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


@dataclass
class User:
    id: int
    username: str
    discriminator: int
    avatar: str
    banner: str
    bot: bool

    def __init__(self, state, data):
        self._state = state
        self.id = int(data['id'])
        self.username = data['username']
        self.discriminator = int(data['discriminator'])
        self.avatar = data['avatar']
        self.banner = data.get('banner')
        self.bot = data.get('bot', False)

    def __str__(self):
        if self.discriminator == 0:
            return '{self.username}'.format(self=self)
        return '{self.username}#{self.discriminator}'.format(self=self)


@dataclass
class ClientUser:
    id: int
    username: str
    discriminator: int
    avatar: str
    banner: str
    email: str
    verified: bool
    premium_type: int

    def __init__(self, user, data):
        self._state = user._state
        self.id = user.id
        self.username = user.username
        self.discriminator = user.discriminator
        self.banner = user.banner
        self.avatar = user.avatar
        self.email = data['email']
        self.verified = data['verified']
        self.premium_type = data['premium_type']

    def __str__(self):
        if self.discriminator == 0:
            return '{self.username}'.format(self=self)
        return '{self.username}#{self.discriminator}'.format(self=self)
