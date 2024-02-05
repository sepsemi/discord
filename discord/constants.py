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

API_VERSION = 9

# Z_SYNC_FLUSH suffix
ZLIB_SUFFIX = b'\x00\x00\xff\xff'

# Set a read, write limit of 15 MiB
WEBSOCKET_SIZE_LIMIT = (1024 * 1024) * 16

WEBSOCKET_CONFIGURATION = {
    'open_timeout': None,
    'close_timeout': None,
    'ping_timeout': 2.5,    # Time to Wait for a response
    'ping_interval': 10.0,  # Time to wait between sending a ping request
    'max_size': WEBSOCKET_SIZE_LIMIT,
    'read_limit': WEBSOCKET_SIZE_LIMIT,
    'write_limit': WEBSOCKET_SIZE_LIMIT
}

TOKEN_ID_LENGTH = 12

# Max time we wait for receiving anything
HEARTBEAT_TIMEOUT = 45.0

HTTP_API_URL = 'https://discord.com/api/v{version}'.format(version=API_VERSION)
