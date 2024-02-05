discord
==========
A modern, easy to use, API wrapper for Discord User Accounts


Key Features
-------------
- Modern Pythonic API using ``async`` and ``await``.
- Proper rate limit handling.
- Optimised in both speed and memory.
- Handles Multiple Accounts

Requirements
-------------
- [Linux](https://www.debian.org/)
- [Git](https://git-scm.com/)
- [python >= 3.7](https://www.python.org/downloads/release/python-370/)

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
    python3 -m pipenv shell

    # Install the required project dependencies
    python pipenv install
    
    # Run the application
    python main.py
````

