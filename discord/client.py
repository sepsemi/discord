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


from asyncio import (
    sleep,
    gather,
    all_tasks,
    create_task,
    get_event_loop,
    new_event_loop,
    set_event_loop
)

from logging import getLogger

from .state import ConnectionState

from .gateway import (
    DiscordWebsocket,
    ReconnectWebSocket
)

from .iterators import (
    HistoryIterator,
    SearchIterator
)

from .http import HTTPClient

DEFAULT_SLEEP_TIME = 1

_log = getLogger(__name__)


class Client:

    def __init__(self, **options):
        self.token = None
        self.loop = self._get_event_loop(options)

        self._websocket = None
        self._connection = None

    def _get_event_loop(self, options):
        """Return a event loop"""

        if 'loop' in options:
            return options['loop']

        loop = new_event_loop()
        set_event_loop(loop)
        return loop

    def _get_connection(self):
        """Return a ConnectionState"""

        return ConnectionState(
            loop=self.loop,
            token=self.token,
            dispatch=self.dispatch,
            http=HTTPClient(client=self)
        )

    def _get_websocket(self, parameters):
        """Return a DiscordWebsocket"""

        return DiscordWebsocket(
            client=self,
            parameters=parameters
        )

    def _schedule_event(self, coro, event_name, *args, **kwargs):
        # Schedules the task
        return create_task(coro(*args, **kwargs), name=event_name)

    def dispatch(self, event, *args, **kwargs):
        method = 'on_{}'.format(event)

        try:
            coro = getattr(self, method)
        except AttributeError:
            return None

        self._schedule_event(coro, method, *args, **kwargs)

    @property
    def channels(self):
        return (channel for channel in self._connection._channels.values())

    @property
    def user(self):
        return self._connection._user

    @property
    def users(self):
        return (user for user in self._connection._users.values())

    def history(self, channel):
        """Get the history of a channel"""

        iterator = HistoryIterator(
            state=self._connection,
            channel=channel
        )

        return iterator.history(limit=9999)

    def search(self, guild=None, channel=None, **kwargs):
        """Get the results for a query"""

        iterator = SearchIterator(
            state=self._connection,
            guild=guild,
            channel=channel
        )

        return iterator.search(**kwargs)

    async def delete_message(self, channel_id, message_id):
        return await self._connection.http.delete_message(
            channel_id=channel_id,
            message_id=message_id
        )

    def _update_parameters(self, params, resume):
        params.update(
            resume=resume,
            uri=self._websocket.uri,
            sequence=self._websocket.sequence,
            session=self._websocket.session_id,
        )

        _log.debug(
            'Set params to: %s',
            params,
            extra={
                'className': self.__class__.__name__,
                'clientId': self._connection.id,
            }
        )

    async def connect(self, reconnect=True):
        parameters = {'initial': True}

        # Everything is stored here, never EVER create a new instance
        self._connection = self._get_connection()

        while True:
            self._websocket = self._get_websocket(parameters)

            # Poll the websocket for events
            try:
                await self._websocket.poll()
            except ReconnectWebSocket as exception:
                _log.debug(
                    'Got a request to %s the websocket.',
                    exception.op,
                    extra={
                        'className': self.__class__.__name__,
                        'clientId': self._connection.id,
                    }
                )

                # Updfate the parameters based on the exception resume
                self._update_parameters(parameters, exception.resume)
                continue

            if reconnect is False:
                return None

            # Always resume
            self._update_parameters(parameters, resume=True)

            await sleep(DEFAULT_SLEEP_TIME)

    async def start(self, token, reconnect=True):
        """Starts the connection"""

        # Set the internal token
        self.token = token

        await self.connect(reconnect=reconnect)

    def run(self, token, reconnect=True):
        """Starts the connection and handles the rest"""

        # Set the internal token
        self.token = token

        coro = self.connect(reconnect=reconnect)

        try:
            self.loop.run_until_complete(coro)
        except KeyboardInterrupt:
            for task in all_tasks(loop=self.loop):
                task.cancel()

            # Run the event loop until all tasks are done
            self.loop.run_until_complete(
                gather(
                    *all_tasks(loop=self.loop),
                    return_exceptions=True
                )
            )

        finally:
            self.loop.close()
