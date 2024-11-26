import asyncio
import logging
import re
from pyrogram import Client
from datetime import datetime
from transformers import pipeline
from db.db_connection import get_connection

with open('C:\\Users\\matve\\PycharmProjects\\SII_Lab_1\\project\\api-logging.txt', 'r') as file:
    api = file.read().strip().split(':')
api_id = int(api[0])
api_hash = api[1]

donors_id = '@posecretuvsemusvetu12'

# Инициализация моделей для анализа
sentiment_analyzer = pipeline("sentiment-analysis")
topic_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

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


# Анализ тональности текста
def analyze_sentiment(text: str) -> str:
    """
    Анализ тональности текста.
    :param text: Исходный текст
    :return: Тональность текста ('POSITIVE', 'NEGATIVE', 'NEUTRAL').
    """
    result = sentiment_analyzer(text)
    return result[0]["label"]


# Предсказание темы текста
def predict_topic(text: str) -> str:
    """
    Предсказание темы текста.
    :param text: Исходный текст
    :return: Наиболее вероятная тема текста.
    """
    candidate_labels = ["спорт", "политика", "развлечения", "технологии", "путешествия", "еда", "мода"]
    result = topic_classifier(text, candidate_labels)
    return result["labels"][0]


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
        else:  # Если пользователя нет, добавляем его
            cursor.execute('INSERT INTO "User" ("username") VALUES (%s) RETURNING "id"', (user_name,))
            user = cursor.fetchone()
            user_id = user['id'] if user else None

        conn.commit()
    except Exception as e:
        conn.rollback()
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
        cursor.execute(
            'INSERT INTO "Message" ("user_id", "text", "date") VALUES (%s, %s, %s) RETURNING "id"',
            (user_id, message_text, message_time)
        )
        message_id = cursor.fetchone()["id"]
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Error occurred while adding message: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

    return message_id


# Добавление аналитики в таблицу MessageAnalytic
def add_message_analytics_to_db(message_id: int, cleaned_text: str, sentiment: str, topic: str):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'INSERT INTO "MassageAnalytic" (message_id, text_cleaned, predicted_tonality, predicted_topic) VALUES (%s, %s, %s, %s)',
            (message_id, cleaned_text, sentiment, topic)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Error occurred while adding message analytics: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


# Парсинг сообщений
async def fetch_new_messages(client: Client):
    last_saved_id = load_last_saved_id()
    max_message_id = last_saved_id

    async for message in client.get_chat_history(donors_id, offset_id=0):
        if message.id > last_saved_id:
            user_name = (
                message.from_user.username if message.from_user and message.from_user.username
                else message.from_user.first_name if message.from_user
                else "Unknown User"
            )
            message_text = message.text if message.text is not None else ""

            # Пропускаем сообщения с длиной текста менее 3 символов
            if len(message_text.strip()) < 3:
                continue

            message_time = message.date.strftime("%Y-%m-%d %H:%M:%S")
            user_id = add_user_to_db(user_name)
            message_id = add_message_to_db(user_id, message_text, message_time)

            normalized_text = normalize_text(message_text)
            sentiment = analyze_sentiment(normalized_text)
            topic = predict_topic(normalized_text)

            add_message_analytics_to_db(message_id, normalized_text, sentiment, topic)
            logging.info(f"Processed message ID: {message.id}, Sentiment: {sentiment}, Topic: {topic}")

            if message.id > max_message_id:
                max_message_id = message.id

    save_last_saved_id(max_message_id)


# Основной цикл
async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    async with Client("user_bot", api_id=api_id, api_hash=api_hash) as client:
        await fetch_new_messages(client)


if __name__ == "__main__":
    asyncio.run(main())
