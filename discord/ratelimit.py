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
