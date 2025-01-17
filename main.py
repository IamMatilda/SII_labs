import asyncio
import logging
import configparser
from pyrogram import Client
from project.telegram_parser import fetch_new_messages

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return int(config['pyrogram']['api_id']), config['pyrogram']['api_hash']

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    api_id, api_hash = load_config()

    async with Client("user_bot", api_id=api_id, api_hash=api_hash) as client:
        await fetch_new_messages(client)

if __name__ == "__main__":
    asyncio.run(main())
