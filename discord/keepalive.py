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


from asyncio import sleep
from logging import getLogger
from time import perf_counter

from .util import to_json

from .enum import GatewayOpcode

_log = getLogger(__name__)


class AsyncKeepaliveHandler:
    MAX_LATENCY = 10

    def __init__(self, gateway, interval):
        self.gateway = gateway
        self.interval = interval

        self.latency = 0.0
        self.last_ack = perf_counter()
        self.last_send = perf_counter()
        self.last_recv = perf_counter()

        # Predefined messages
        self.msg = 'Gateway acknowledged heartbeat, sequence=%s'
        self.behind_msg = 'Gateway acknowledged late %.1fs behind'
        self.unresponsive_msg = 'has stopped responding to gateway, closing'

    def is_connected(self):
        """Check if the websocket connection is still open"""

        return self.gateway._websocket.open

    def tick(self):
        self.last_recv = perf_counter()

    def ack(self):
        ack_time = perf_counter()

        self.last_ack = ack_time
        self.latency = ack_time - self.last_send

        if self.latency > self.MAX_LATENCY:
            return _log.warning(
                self.behind_msg,
                self.latency,
                extra={
                    'className': self.__class__.__name__,
                    'clientId': self.gateway.id,
                }
            )

        return _log.debug(
            self.msg,
            self.gateway.sequence,
            extra={
                'className': self.__class__.__name__,
                'clientId': self.gateway.id,
            }
        )

    def get_payload(self):
        return {
            'op': GatewayOpcode.HEARTBEAT.value,
            'd': self.gateway.sequence
        }

    async def send_heartbeat(self):
        payload = self.get_payload()

        # Bypass ratelimit
        await self.gateway._websocket.send(to_json(payload))

    async def run(self):
        while self.is_connected():
            if self.last_recv + self.gateway._max_heartbeat_timeout < perf_counter():
                _log.warning(
                    self.unresponsive_msg,
                    extra={
                        'className': self.__class__.__name__,
                        'clientId': self.gateway.id,
                    }
                )

                # Close the gateway
                return await self.gateway.close()

            await self.send_heartbeat()

            self.last_send = perf_counter()
            await sleep(self.interval)
