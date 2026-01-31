# dcsv-py

Ultra High Performance, Stackless Discord Library for Python

## Features

- **Stackless Architecture**: Zero caching, 100% control
- **Auto-Sharding**: Built-in, zero-config sharding
- **Memory Efficient**: Minimal RAM usage
- **Raw Events**: Listen to any Discord event directly
- **Interaction Focused**: Optimized for Slash Commands

## Installation

```bash
pip install aiohttp websockets
```

## Quick Start

```python
import asyncio
from dcsv import Client, GatewayIntentBits

client = Client({
    'intents': GatewayIntentBits.GUILDS | GatewayIntentBits.GUILD_MESSAGES,
    'shards': 'auto'
})

@client.event
async def on_ready(user):
    print(f"Logged in as {user['username']}")

@client.event
async def on_messageCreate(message):
    if message.get('content') == '!ping':
        await client.create_message(
            message['channel_id'], 
            {'content': 'Pong!'}
        )

asyncio.run(client.login('YOUR_TOKEN'))
```

## License

MIT
