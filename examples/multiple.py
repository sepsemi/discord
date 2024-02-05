from asyncio import (
    wait,
    set_event_loop,
    new_event_loop,
)

from discord import Client


class DiscordClient(Client):

    async def on_ready(self):
        print('Client username={self.user} ready'.format(self=self))

    async def on_message(self, ctx):
        print('client={self.user.name}, author={ctx.author}, content={ctx.content}'.format(
            ctx=ctx,
            self=self
        ))


DISCORD_TOKENS = [
    'yourtoken-1',
    'yourtoken-2'
]


async def main(loop):
    tasks = []

    for token in DISCORD_TOKENS:
        client = DiscordClient(loop=loop)
        task = loop.create_task(client.start(token))
        tasks.append(task)

    await wait(tasks)


loop = new_event_loop()
set_event_loop(loop)
loop.run_until_complete(main(loop))
