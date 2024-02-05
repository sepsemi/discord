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


from .util import (
    from_json,
    to_json,
    Connect,
    minutes_elapsed_timestamp
)


from asyncio import (
    wait_for,
    TimeoutError
)
from logging import getLogger

from zlib import decompressobj


from .constants import (
    ZLIB_SUFFIX,
    WEBSOCKET_CONFIGURATION
)

from .enum import (
    GatewayOpcode,
    GatewayEvent
)

from .subscriber import GuildSubscriber
from .ratelimit import GatewayRatelimiter
from .keepalive import AsyncKeepaliveHandler

_log = getLogger(__name__)


class DiscordPacket:
    __slots__ = (
        'code',
        'sequence',
        'event',
        'data'
    )

    def __init__(self, data):
        self.code = data['op']
        self.sequence = data['s'] if 's' in data.keys() else None
        self.event = data['t'] if 't' in data.keys() else None
        self.data = data['d'] if 'd' in data.keys() else None

    def __str__(self):
        return 'code={self.code}, sequence={self.sequence}, event={self.event}, data={self.data}'.format(self=self)


class ReconnectWebSocket(Exception):

    def __init__(self, resume=True):
        self.resume = resume
        self.op = 'RESUME' if resume else 'IDENTIFY'


class DiscordWebsocket:
    API_VERSION = 9
    DEFAULT_GATEWAY = 'wss://gateway.discord.gg'

    def __init__(self, client, parameters):
        self.loop = client.loop
        self.id = client._connection.id
        self.token = client._connection.token
        self.device = client._connection.device
        self.uri = self._get_gatway_uri(parameters)

        self._guild_subscriber = None
        self._rate_limiter = GatewayRatelimiter()

        # Client connection parsers
        self._keep_alive = None
        self._parsers = client._connection.parsers

        # Max timeout after not receiving anything
        self._max_heartbeat_timeout = client._connection.heartbeat_timeout

        # Previous state(If its set)
        self._initial = parameters['initial']
        self.resume_set = parameters.get('resume', False)
        self.sequence = parameters.get('sequence', None)
        self.session_id = parameters.get('session', None)

        # Setup the buffers to process messages
        self._reset_buffer()

        # Register the opcode routes
        self.op_code_routes = {
            GatewayOpcode.HELLO.value: self.process_hello,
            GatewayOpcode.DISPATCH.value: self.process_dispatch,
            GatewayOpcode.RECONNECT.value: self.process_reconnect,
            GatewayOpcode.HEARTBEAT.value: self.process_heartbeat,
            GatewayOpcode.HEARTBEAT_ACK.value: self.process_heartbeat,
            GatewayOpcode.INVALIDATE_SESSION.value: self.process_invalidate_session,
        }

        # Register the event routes
        self.event_routes = {
            GatewayEvent.READY.value: self.process_ready,
            GatewayEvent.RESUMED.value: self.process_resumed,
            GatewayEvent.SESSIONS_REPLACE.value: self.process_sessions_replace,
            GatewayEvent.READY_SUPPLEMENTAL.value: self.process_ready_supplemental,
            GatewayEvent.GUILD_MEMBERS_CHUNK.value: self.process_guild_members_chunk
        }

    def _reset_buffer(self):
        self._zlib = decompressobj()
        self._buffer = bytearray()

    def _get_gatway_uri(self, parameters):
        # Set the encoding, compresison options
        options = '/?encoding=json&v={version}&compress=zlib-stream'.format(
            version=self.API_VERSION
        )

        return parameters.get('uri', self.DEFAULT_GATEWAY) + options

    def _get_connection(self):
        return Connect(
            uri=self.uri,
            user_agent_header=self.device.headers['browser_user_agent'],
            ** WEBSOCKET_CONFIGURATION
        )

    def _get_keep_alive(self, interval):
        """Create a AsyncKeepaliveHandler and return task + handler instance"""

        handler = AsyncKeepaliveHandler(
            gateway=self,
            interval=interval
        )

        return {
            'handler': handler,
            'task': self.loop.create_task(handler.run())
        }

    def _get_guild_subscriber(self, guilds):
        """Creates a GuildSubscriber and return task + Subscriber"""
        handler = GuildSubscriber(gateway=self)

        return {
            'handler': handler,
            'task': self.loop.create_task(handler.process(guilds))
        }

    def _extract_session_from_replace(self, data):
        """Get the new session id"""

        for session in reversed(data):
            session_id = session['session_id']
            if len(session_id) >= len(self.session_id) and session_id != self.session_id:
                return session_id

        return self.session_id

    async def send(self, payload):
        await self._rate_limiter.block()

        payload = to_json(payload)
        return await self._websocket.send(payload)

    async def close(self, code=1000):
        if self._keep_alive is not None:

            # Cancel the Keepalive task
            self._keep_alive['task'].cancel()

        if self._guild_subscriber is not None:
            self._guild_subscriber['task'].cancel()

        return await self._websocket.close(code=code)

    async def request_guild_members(self, guild_id):
        payload = {
            'op': GatewayOpcode.REQUEST_MEMBERS.value,
            'd': {
                'guild_id': str(guild_id),
                'user_ids': ['748667545002704898'],
                'limit': 0,
            }
        }
        await self.send(payload)

    async def identify(self):
        """Send identify packet to websocket"""

        payload = {
            'op': GatewayOpcode.IDENTIFY.value,
            'd': {
                'token': self.token,
                'capabilities': 1021,
                'properties': {**self.device.headers},
                'compress': False,
                # Need to research
                'client_state': {
                    'guild_hashes': {},
                    'highest_last_message_id': '0',
                    'read_state_version': 0,
                    'user_guild_settings_version': -1,
                    'user_settings_version': -1,
                    'private_channels_version': '0'
                }
            }
        }

        # Set presence
        payload['d']['presence'] = {
            'status': 'idle',
            'since': 0,
            'activities': [],
            'afk': False
        }

        _log.debug(
            'Sending identify packet %s',
            payload,
            extra={
                'className': self.__class__.__name__,
                'clientId': self.id,
            }
        )

        return await self.send(payload)

    async def change_presence(self):
        # Create an elapsed timestamp for exmaple "20-60 minutes"
        elapsed = minutes_elapsed_timestamp(0)
        payload = {
            'op': GatewayOpcode.PRESENCE.value,
            'd': {
                'status': 'idle',
                'since': None,
                'activities': [
                    {
                        'name': 'Assassin\'s Creed III',
                        'type': 0,
                        'application_id': 425434783695503360,
                        'timestamps': {
                            'start': elapsed
                        }
                    }
                ],
                'afk': False
            }
        }
        await self.send(payload)

    async def resume(self):
        """Send resume packet to websocket"""

        payload = {
            'op': GatewayOpcode.RESUME.value,
            'd': {
                'seq': self.sequence,
                'session_id': self.session_id,
                'token': self.token
            }
        }

        _log.debug(
            'Sending resume packet: %s',
            payload,
            extra={
                'className': self.__class__.__name__,
                'clientId': self.id,
            }
        )

        await self.send(payload)

    async def process_guild_members_chunk(self, packet):
        return await self._subscriber.guild_members_chunk(packet.data)

    async def process_ready_supplemental(self, packet):
        print('Processing READY_SUPPLEMENTAL')
        return None

        for merged in packet.data['merged_members']:
            print('-' * 100)
            print(merged)

    async def process_invalidate_session(self, packet):
        _log.warning(
            'Session has been invalidated',
            extra={
                'className': self.__class__.__name__,
                'clientId': self.id,
            }
        )

        if packet.data is True:
            await self.close()
            raise ReconnectWebSocket()

        self.sequence = None
        self.session_id = None

        # Set the uri to the default
        self.uri = self.DEFAULT_GATEWAY

        # Close keepalive
        await self.close(code=1000)
        raise ReconnectWebSocket(resume=False)

    async def process_reconnect(self, packet):
        _log.info(
            'Received RECONNECT opcode',
            extra={
                'className': self.__class__.__name__,
                'clientId': self.id,
            }
        )
        await self.close()
        raise ReconnectWebSocket

    async def process_ready(self, packet):
        self.session_id = packet.data['session_id']
        self.uri = packet.data['resume_gateway_url']

        _log.info(
            'Connected to Gateway session_id=%s',
            self.session_id,
            extra={
                'className': self.__class__.__name__,
                'clientId': self.id,
            }
        )

        # Just change the pressence for now

        await self.change_presence()

        # Register the guilds and subscribe
        guilds = packet.data['guilds']

        self._guild_subscriber = self._get_guild_subscriber(guilds)

    async def process_resumed(self, packet):
        _log.info(
            'Successfully RESUMED session_id=%s',
            self.session_id,
            extra={
                'className': self.__class__.__name__,
                'clientId': self.id,
            }
        )

    async def process_sessions_replace(self, packet):
        new_session_id = self._extract_session_from_replace(packet.data)
        _log.debug(
            'Replacing session_id=%s with=%s',
            self.session_id,
            new_session_id,
            extra={
                'className': self.__class__.__name__,
                'clientId': self.id,
            }
        )

        return None

    async def process_heartbeat(self, packet):
        if packet.code == GatewayOpcode.HEARTBEAT.value:
            _log.debug(
                'Request forcefull hearbeat',
                extra={
                    'className': self.__class__.__name__,
                    'clientId': self.id,
                }
            )

            self._keep_alive['handler'].send_heartbeat()

        # Just acknowlege the heartbeat
        return self._keep_alive['handler'].ack()

    async def process_hello(self, packet):
        interval = packet.data['heartbeat_interval'] / 1000.0

        # Create the keepalive task and keep a reference to the hander and task
        self._keep_alive = self._get_keep_alive(interval)

        if not self.resume_set:
            return await self.identify()

        return await self.resume()

    def dispatch_client_event(self, packet):
        try:
            func = self._parsers[packet.event]
        except KeyError:
            return _log.debug(
                'Unknown event, seq=%d, event=%s',
                self.sequence,
                packet.event,
                extra={
                    'className': self.__class__.__name__,
                    'clientId': self.id,
                }
            )

        return func(packet.data)

    async def process_dispatch(self, packet):
        event = packet.event

        if event in GatewayEvent.values():
            await self.event_routes[event](packet)

        return self.dispatch_client_event(packet)

    async def handle_dispatch_route(self, message):
        packet = DiscordPacket(message)
        op_code = packet.code

        if packet.sequence is not None:
            self.sequence = packet.sequence

        if self._keep_alive:
            self._keep_alive['handler'].tick()

        if op_code in GatewayOpcode.values():
            await self.op_code_routes[op_code](packet)

    def received_message(self, data):
        self._buffer.extend(data)
        data_length = len(data)

        _log.debug(
            'Processing %d byte%s',
            data_length,
            's' if data_length > 1 else '',
            extra={
                'className': self.__class__.__name__,
                'clientId': self.id,
            }
        )

        if data_length < 4 or data[-4:] != ZLIB_SUFFIX:
            return None

        data = self._zlib.decompress(self._buffer)
        self._buffer = bytearray()

        return from_json(data)

    def raise_or_handle(self, exception):
        can_handle_exceptions = (
            'TimeoutError',
            'WebsocketClosedOk'
            'IncompleteReadError',
            'ConnectionClosedError'
        )

        # Get the class name of the Exception
        class_name = exception.__class__.__name__

        if class_name in can_handle_exceptions:
            raise ReconnectWebSocket(resume=True)

        # We cannot handle this Exception so we raise it
        raise exception

    async def poll(self):
        self._websocket = await self._get_connection()
        _log.debug(
            'Connecting to: %s',
            self.uri,
            extra={
                'className': self.__class__.__name__,
                'clientId': self.id,
            }
        )

        while self._websocket.open:
            try:
                data = await wait_for(
                    self._websocket.recv(),
                    timeout=self._max_heartbeat_timeout
                )
            except Exception as exception:
                return self.raise_or_handle(exception)

            message = self.received_message(data)
            await self.handle_dispatch_route(message)
