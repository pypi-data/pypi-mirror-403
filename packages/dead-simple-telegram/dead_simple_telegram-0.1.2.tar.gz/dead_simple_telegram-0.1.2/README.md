# Telegram Post
Telegram Post is a dead simple standalone python library.

It has one purpose: post a message via telegram bot. 

## Dependencies

requests

## Setup
Can use env vars or pass a dictionary at run time. see examples below.

Install from PyPI:

``` bash
pip install dead-simple-telegram
```

# Examples

There are two ways to use this lib. Import from `dead_simple_telegram`:



## With Environmential Vars

Set these values
TELEGRAM_BOT_TOKEN = "your bot api token"
TELEGRAM_CHAT_ID = "chat id for the conversation"
TELEGRAM_TIMEOUT = 5 # optional defaults to 10

``` python
from dead_simple_telegram import TelegramConfig, send_message

config = TelegramConfig.from_env()
message = "This is a message"
send_message(config, message)

```

## With a Dictionary
``` python
from dead_simple_telegram import TelegramConfig, send_message

config = TelegramConfig.from_dict({"bot_token": "YOURTOKEN", "chat_id": "YOURCHATID", "timeout":5})
message = "This is a message"
send_message(config, message)

```
