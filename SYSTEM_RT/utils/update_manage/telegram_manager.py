import asyncio
import html
import os

import telegram
from dotenv import load_dotenv

load_dotenv()


async def send_telegram_message(bot_token, chat_id, message_text, parse_mode=None):
    bot = telegram.Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=message_text)


# Create an event loop and run the asynchronous function


async def send_async_message(message_text):
    # Replace 'YOUR_BOT_TOKEN' with the actual API token of your bot
    bot_token = os.getenv("bot_token")
    chat_id = os.getenv("chat_id")  # Replace with the actual chat ID of your group
    # Set parse_mode to 'Markdown'
    parse_mode = "Markdown"
    loop = asyncio.get_event_loop()
    escaped_message = html.escape(message_text)
    # Run the asynchronous function using asyncio.ensure_future or loop.create_task
    # Choose one of the following lines:
    # task = asyncio.ensure_future(send_telegram_message(bot_token, chat_id, message_text, parse_mode))
    task = loop.create_task(
        send_telegram_message(bot_token, chat_id, escaped_message, parse_mode)
    )
    await task
