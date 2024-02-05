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

from aiohttp import (
    TCPConnector,
    ClientTimeout,
    ClientSession
)

from .util import (
    to_json,
    from_json
)

from .constants import HTTP_API_URL
from .ratelimit import HTTPRatelimiter

from urllib.parse import quote as _uriquote


class Route:

    def __init__(self, method, path, **parameters):
        self.path = path
        self.method = method

        url = HTTP_API_URL + self.path

        if parameters:
            url = url.format_map({k: _uriquote(v) if isinstance(
                v, str) else v for k, v in parameters.items()})

        self.url: str = url


class HTTPClient:
    DNS_CACHE_TTL = 300
    MAX_SIZE_POOL = 10
    ESTABLISHED_CONNECTION_TIMEOUT = 1800.0

    def __init__(self, client):
        self.id = None
        self.loop = client.loop
        self.client = client

        self._limiter = HTTPRatelimiter(id=self.id)
        self.__session = self.get_aiohttp_session()

    def get_aiohttp_client_timeout(self):
        return ClientTimeout(
            total=None,
            connect=None,
            sock_read=None,
            sock_connect=self.ESTABLISHED_CONNECTION_TIMEOUT
        )

    def get_aiohttp_connector(self):
        return TCPConnector(
            loop=self.loop,
            ttl_dns_cache=self.DNS_CACHE_TTL,
            force_close=True,
            limit=self.MAX_SIZE_POOL
        )

    def get_aiohttp_session(self):
        return ClientSession(
            loop=self.loop,
            connector=self.get_aiohttp_connector(),
            timeout=self.get_aiohttp_client_timeout()
        )

    def _can_handle_code(self, code):
        return code in (200, 204, 429)

    async def _do_request_cycle(self, method, url, **kwargs):
        method = method.lower()

        # Get the method from aiohttp session
        func = getattr(self.__session, method)

        while True:

            async with self._limiter:
                response = await func(url, **kwargs)

                text = await response.text()

                if response.status == 429:
                    self._limiter.set(from_json(text))
                    continue

                if not self._can_handle_code(response.status):
                    return text

                if not text:
                    return None

                if response.status in (200, 204):
                    return from_json(text)

    def request(self, route, **kwargs):
        method = route.method
        url = route.url

        # Get the device properties used by the client
        device = self.client._connection.device

        headers = {
            'user-agent': device.headers['browser_user_agent'],
            'x-super-properties': device.x_super_properties,
            'authorization': self.client.token
        }

        if 'json' in kwargs:
            headers['content-type'] = 'application/json'
            kwargs['data'] = to_json(kwargs.pop('json'))

        kwargs['headers'] = headers

        return self._do_request_cycle(method, url, **kwargs)

    def history(self, channel):
        channel_id = str(channel.id)

        route = Route(
            'GET', '/channels/{channel_id}/messages',
            channel_id=channel_id
        )

        return self.request(route)

    def delete_message(self, channel_id, message_id):
        route = Route(
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}',
            channel_id=channel_id,
            message_id=message_id
        )

        return self.request(route)
