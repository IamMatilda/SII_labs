import asyncio
import logging
import configparser
from pyrogram import Client
from project.telegram_parser import fetch_new_messages

# Чтение конфигурации из файла
def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    api_id = int(config['pyrogram']['api_id'])
    api_hash = config['pyrogram']['api_hash']
    return api_id, api_hash

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Загружаем конфигурацию
    api_id, api_hash = load_config()

    # Создаем клиент Pyrogram с параметрами из конфигурации
    async with Client("user_bot", api_id=api_id, api_hash=api_hash) as client:
        await fetch_new_messages(client)

if __name__ == "__main__":
    asyncio.run(main())
