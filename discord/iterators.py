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

from .http import Route
from .message import message_factory


class HistoryIterator:

    def __init__(self, state, channel):
        self.state = state
        self.channel = channel

    def fetch_channel_messages(self, channel_id):
        """Fetches the messages for a private channel"""

        route = Route(
            'GET', '/channels/{channel_id}/messages',
            channel_id=channel_id,
        )

        return self.state.http.request(route)

    async def _strategy_before(self, channel, before_id):
        before_id = before_id if before_id else None

        route = Route(
            'GET', '/channels/{channel_id}/messages',
            channel_id=channel.id
        )

        parameters = {
            'before': before_id
        }

        if before_id is None:
            del parameters['before']

        data = await self.state.http.request(route, params=parameters)

        if isinstance(data, list) and len(data) > 0:
            # If we get data, get the latest id
            before_id = data[-1]['id']

        return data, before_id

    async def history(self, limit):
        before_id = None

        retrieve_strategy = self._strategy_before

        while True:
            data, before_id = await retrieve_strategy(self.channel, before_id=before_id)

            if not isinstance(data, list) or not len(data) > 0:
                return

            for message_data in data:
                message = message_factory(None, self.channel, message_data)

                if message is None:
                    continue

                yield message


class SearchIterator:
    MESSAGES = 'messages'
    HISTORICAL_INDEX = 'doing_deep_historical_index'

    def __init__(self, state, guild, channel):
        self.state = state
        self.guild = guild
        self.channel = channel

        self.offset = 0
        self.processed = 0
        self.total_results = None

    def clear(self):
        self.offset = 0
        self.processed = 0

    def _get_context_route(self, value, context_id):
        return Route(
            'GET',
            '/{value}/{context_id}/messages/search',
            value=value,
            context_id=context_id
        )

    def _process_chunk(self, chunk):
        """Processes a chunk of messages"""

        for message_data in chunk:
            # Create the message from the data we have recieved
            message = self.state._create_message(message_data)
            self.processed += 1

            if message is None:
                continue

            yield message

    def _get_route(self):
        """Gets the correct route based on the guild being pressent of not"""

        if not self.guild:
            return self._get_context_route('channels', self.channel.id)

        return self._get_context_route('guilds', self.guild.id)

    async def search(self, **kwargs):
        """Searches for messages from the specified parameters"""

        self.clear()
        route = self._get_route()

        # Always include NSFW
        kwargs['include_nsfw'] = 1

        while True:
            if self.offset > 0:
                kwargs['offset'] = self.offset

            data = await self.state.http.request(route, params=kwargs)

            if isinstance(data, str):
                return

            # This is not a search result
            if self.HISTORICAL_INDEX not in data.keys():
                return

            if self.total_results is None:
                self.total_results = data['total_results']

            # Wait until we get a result from the search
            if data[self.HISTORICAL_INDEX] is True:
                continue

            # We failed to get a response, so we stop here
            if self.MESSAGES not in data.keys():
                return

            # We could not get any results despite all our efforts
            if self.total_results == 0:
                return

            chunks = data[self.MESSAGES]

            if len(chunks) < 0:
                return

            for chunk in chunks:
                for message in self._process_chunk(chunk):
                    yield message

                if self.processed >= self.total_results:
                    return

            self.offset += 25
