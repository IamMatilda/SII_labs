import asyncio
import logging
import re
from pyrogram import Client
from datetime import datetime
from db.db_connection import get_connection

with open('C:\\Users\\matve\\PycharmProjects\\SII_Lab_1\\project\\api-logging.txt', 'r') as file:
    api = file.read().strip().split(':')
api_id = int(api[0])
api_hash = api[1]

donors_id = '@posecretuvsemusvetu12'

# Загрузка сохранённого ID
def load_last_saved_id():
    try:
        with open('last_message_id.txt', 'r') as file:
            return int(file.read().strip())
    except FileNotFoundError:
        return 0  # Если файла нет, начинаем с начала


# Сохранение самого большого ID
def save_last_saved_id(last_message_id):
    with open('last_message_id.txt', 'w') as file:
        file.write(str(last_message_id))
    logging.info(f"Saved last_saved_id: {last_message_id}")


# Нормализация текста: удаление ссылок, спецсимволов и приведение к нижнему регистру
def normalize_text(text: str) -> str:
    """
    Простая нормализация текста: удаление ссылок, спецсимволов и приведение к нижнему регистру.
    :param text: Исходный текст
    :return: Нормализованный текст
    """
    if text is None:  # Проверяем на None
        return ""
    # Удаляем URL
    text = re.sub(r'http\S+|www\S+', '', text)
    # Удаляем спецсимволы
    text = re.sub(r'[^\w\s]', '', text)
    # Приводим текст к нижнему регистру
    return text.strip().lower()


# Добавление пользователя в базу данных
def add_user_to_db(user_name: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Проверяем, есть ли пользователь в базе данных
        cursor.execute('SELECT id FROM "User" WHERE "username" = %s', (user_name,))
        user = cursor.fetchone()

        if user:  # Если пользователь найден
            user_id = user['id']  # Используем ключ 'id', если результат - словарь
            logging.info(f"User found with ID: {user_id}")
        else:  # Если пользователя нет, добавляем его
            cursor.execute('INSERT INTO "User" ("username") VALUES (%s) RETURNING "id"', (user_name,))
            user = cursor.fetchone()
            if user:
                user_id = user['id']  # Используем ключ 'id' для извлечения
                logging.info(f"User inserted with ID: {user_id}")
            else:
                raise Exception("Failed to retrieve user ID after insertion.")

        conn.commit()

    except Exception as e:
        conn.rollback()  # Откат транзакции в случае ошибки
        logging.error(f"Error occurred while adding user: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

    return user_id



# Добавление сообщения в таблицу Message
def add_message_to_db(user_id: int, message_text: str, message_time: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Вставляем сообщение
        cursor.execute(
            'INSERT INTO "Message" ("user_id", "text", "date") VALUES (%s, %s, %s) RETURNING "id"',
            (user_id, message_text, message_time)
        )

        # Получаем ID вставленного сообщения
        message_data = cursor.fetchone()
        if message_data:
            message_id = message_data['id']  # Используем ключ 'id' для извлечения данных
            logging.info(f"Message inserted with ID: {message_id}")
        else:
            raise Exception("Failed to retrieve message ID after insertion.")

        conn.commit()

    except Exception as e:
        conn.rollback()  # Откат транзакции в случае ошибки
        logging.error(f"Error occurred while adding message: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

    return message_id



# Добавление аналитики в таблицу MessageAnalytic
def add_message_analytics_to_db(message_id: int, cleaned_text: str):
    conn = get_connection()
    cursor = conn.cursor()

    # Вставляем нормализованный текст
    cursor.execute(
    'INSERT INTO "MassageAnalytic" (message_id, text_cleaned) VALUES (%s, %s)',
        (message_id, cleaned_text)
    )

    conn.commit()
    cursor.close()
    conn.close()


# Парсинг сообщений
async def fetch_new_messages(client: Client):
    """
    Асинхронная функция для получения новых сообщений из чата.
    :param client: клиент Pyrogram
    """
    # Загружаем последний сохранённый ID
    last_saved_id = load_last_saved_id()
    logging.info(f"Loaded last_saved_id: {last_saved_id}")

    # Для хранения самого большого ID
    max_message_id = last_saved_id

    # Парсим сообщения
    async for message in client.get_chat_history(donors_id, offset_id=0):
        if message.id > last_saved_id:  # Проверяем только новые сообщения
            user_name = (
                message.from_user.username if message.from_user and message.from_user.username
                else message.from_user.first_name if message.from_user
                else "Unknown User"
            )
            message_time = message.date.strftime("%Y-%m-%d %H:%M:%S")

            # Добавляем пользователя в базу данных (если он новый)
            user_id = add_user_to_db(user_name)

            # Проверяем текст сообщения на None
            message_text = message.text if message.text is not None else ""

            # Добавляем сообщение в таблицу Message
            message_id = add_message_to_db(user_id, message_text, message_time)

            # Нормализуем текст
            normalized_text = normalize_text(message_text)

            # Добавляем аналитику для сообщения в таблицу MessageAnalytic
            add_message_analytics_to_db(message_id, normalized_text)

            logging.info(f"Saved message ID: {message.id}, User: {user_name}")

            # Обновляем максимальный ID
            if message.id > max_message_id:
                max_message_id = message.id

    # Сохраняем самый большой ID
    save_last_saved_id(max_message_id)

# Основной цикл
async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    async with Client("user_bot", api_id=api_id, api_hash=api_hash) as client:
        await fetch_new_messages(client)


if __name__ == "__main__":
    asyncio.run(main())
