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


from time import time
from logging import getLogger

from asyncio import (
    sleep,
    Lock
)

_log = getLogger(__name__)


class GatewayRatelimiter:
    def __init__(self, count=110, per=60.0):
        self.max = count
        self.remaining = count
        self.window = 0.0
        self.per = per
        self.lock = Lock()

    def is_ratelimited(self):
        current = time()
        if current > self.window + self.per:
            return False
        return self.remaining == 0

    def get_delay(self):
        current = time()

        if current > self.window + self.per:
            self.remaining = self.max

        if self.remaining == self.max:
            self.window = current

        if self.remaining == 0:
            return self.per - (current - self.window)

        self.remaining -= 1
        return 0.0

    async def block(self) -> None:
        async with self.lock:
            delta = self.get_delay()
            if delta:
                _log.warning(
                    'WebSocket is ratelimited, waiting %.2f seconds',
                    delta,
                    extra={
                        'className': self.__class__.__name__,
                        'clientId': 0,
                    }
                )

                await sleep(delta)


class HTTPRatelimiter:
    DEFAULT_TIMEOUT = 10

    def __init__(self, id):
        self.id = id
        self.lock = Lock()
        self.after = 0.0
        self.last = time()

    def set(self, data):
        """Set the retry after value."""

        self.last = time()
        if 'retry_after' in data:
            retry_after = data['retry_after']
        else:
            retry_after = self.DEFAULT_TIMEOUT

        self.after = retry_after

    def get_delay(self):
        """Get the remaining delay in seconds."""

        current = time()
        if (current - self.last) >= self.after:
            self.after = 0.0

        return self.after

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def __aenter__(self):

        async with self.lock:
            delta = self.get_delay()

            if delta <= 0:
                return None

            _log.warning(
                'Ratelimited for %.2f seconds',
                delta,
                extra={
                    'className': self.__class__.__name__,
                    'clientId': self.id,
                }
            )

            await sleep(delta)
