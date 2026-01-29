# Wokki Chat SDK

Python SDK to make bots for **Wokki Chat** easily and asynchronously.  
This library lets you create bots that can send and receive messages, respond to events, and interact with the Wokki Chat platform programmatically.

## Features

- Connect to Wokki Chat using **WebSockets**.
- Send and receive messages in real-time.
- Async-friendly, built on **Python `asyncio`**.
- Easy integration into Python projects.
- Designed to simplify bot creation for developers.

## Installation

Install via pip:

```bash
pip install wokki-chat-sdk
```

## Quick Start
```python
import dotenv, os
from wokkichat import Bot, ctx

dotenv.load_dotenv()
bot = Bot(os.environ["TOKEN"])

@bot.command()
async def echo(c: ctx, text: str):
    await c.reply(f"Echoed: {text}")

bot.connect()
```
With just a few lines, your bot can respond to commands like echo on Wokki Chat.

## Creating a Bot

Before using the SDK, you need to create a bot on Wokki Chat:

1. Go to [Wokki Chat Developer Bots](https://chat.wokki20.nl/developer/bots).  
2. Log in if prompted.  
3. Click the **Create New Bot** button.  
4. Enter a name for your bot and optionally choose an icon.  
5. After creation, click the **Copy Token** button to get your bot token.  
6. Save this token - you’ll use it in your code as the bot’s authentication token.

## License
This project is licensed under the Apache-2.0 License. See the [LICENSE](https://github.com/levkris/Wokki-Chat-Python-SDK/blob/main/LICENSE) file for details.