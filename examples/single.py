from discord import Client


class DiscordClient(Client):

    async def on_ready(self):
        print('Client username={self.user} ready'.format(self=self))

    async def on_message(self, ctx):
        print('author={ctx.author}, content={ctx.content}'.format(ctx=ctx))


client = DiscordClient()

client.run('yourtoken')
