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


import msgspec
import datetime
from websockets.client import connect


# Define json_function alias
to_json = msgspec.json.encode
from_json = msgspec.json.decode

# Define websocket alias
Connect = connect


DISCORD_EPOCH = 1420070400000


def yield_token(path):
    with open(path) as fp:
        for line in fp.readlines():
            yield line.rstrip()


def minutes_elapsed_timestamp(value):
    now = datetime.datetime.now(datetime.timezone.utc)
    elasped = now - datetime.timedelta(minutes=value)
    return round(elasped.timestamp() * 1000)


def snowflake_time(id):
    timestamp = ((id >> 22) + DISCORD_EPOCH) / 1000
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
