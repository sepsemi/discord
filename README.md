## Pinacle of Discord Selfbotting

## Notes
This is just a DIY project:
1. Expect bugs
2. Late updates if any
3. No support

Unamed Library
==========
A modern, easy to use, API wrapper for Discord User Accounts

Key Features
-------------
- Modern Pythonic API using ``async`` and ``await``.
- Proper rate limit handling.
- Optimised in both speed and memory.
- Handles Multiple Accounts
- Prevents detection of user account automation

Requirements
-------------
- [Linux](https://www.debian.org/)
- [Git](https://git-scm.com/)
- [python](https://www.python.org/downloads/release/python-370/) >= 3.7

Dependencies
-------------
- [Asyncio](https://docs.python.org/3/library/asyncio.html)
- [Aiohttp](https://docs.aiohttp.org/en/stable/)
- [Websockets](https://websockets.readthedocs.io/en/stable/faq/asyncio.html)
- [Msgspec](https://jcristharif.com/msgspec/)

Installing
-------------
```bash
 
    # Close the source code, of the project
    git clone git@github.com:sepsemi/discord.git
    cd discord/

    # Move the example file into the Current Working Directory
    cp ./examples/single.py ./main.py
    
    # Install pipenv for easier dependecy management.
    python3 -m pip install pipenv

    # Start a Pipenv shell sperating our dependecies from the host.
    python3 -m pipenv shell

    # Install the required project dependencies
    python pipenv install
    
    # Run the application
    python main.py
```

Quick Example
--------------
```py
from discord import Client


class DiscordClient(Client):

    async def on_ready(self):
        print('Client username={self.user} ready'.format(self=self))

    async def on_message(self, ctx):
        print('author={ctx.author}, content={ctx.content}'.format(ctx=ctx))


client = DiscordClient()

client.run('yourtoken')
```

