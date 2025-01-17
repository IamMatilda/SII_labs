import asyncio
import logging
import re
from pyrogram import Client
from datetime import datetime
from transformers import pipeline
from db.db_connection import get_connection
from prometheus_client import start_http_server, Counter, Gauge
import time
import psutil

# Инициализация Prometheus метрик
processed_messages = Counter("processed_messages", "Количество обработанных сообщений")
active_users = Gauge("active_users", "Количество активных пользователей")
cpu_usage = Gauge("cpu_usage", "Использование CPU в процентах")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования
    format="%(asctime)s - %(levelname)s - %(message)s",  # Формат записи
    handlers=[
        logging.FileHandler("app.log"),  # Запись логов в файл
        logging.StreamHandler()  # Вывод логов в консоль
    ]
)

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
    if text is None:
        return ""
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip().lower()


# Анализ тональности текста
def analyze_sentiment(text: str) -> str:
    result = sentiment_analyzer(text)
    return result[0]["label"]


# Предсказание темы текста
def predict_topic(text: str) -> str:
    candidate_labels = ["спорт", "политика", "развлечения", "технологии", "мода", "мысли", "юмор", "новости", "наука"]
    result = topic_classifier(text, candidate_labels)
    return result["labels"][0]


# Добавление пользователя в базу данных
def add_user_to_db(user_name: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id FROM "User" WHERE "username" = %s', (user_name,))
        user = cursor.fetchone()
        if user:
            user_id = user['id']
        else:
            cursor.execute('INSERT INTO "User" ("username") VALUES (%s) RETURNING "id"', (user_name,))
            user = cursor.fetchone()
            user_id = user['id'] if user else None
            active_users.inc()  # Увеличиваем счетчик активных пользователей
            logging.info(f"Active users: {active_users._value.get()}")
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
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_usage.set(cpu_percent)  # Обновляем метрику Prometheus
            logging.info(f"Current CPU usage: {cpu_percent}%")  # Логируем использование CPU
            logging.info(f"Processed messages: {processed_messages._value.get()}")

            # Обновление метрик
            processed_messages.inc()

            if message.id > max_message_id:
                max_message_id = message.id

    save_last_saved_id(max_message_id)


# Функция для мониторинга CPU


# Основной цикл
async def main():
    async with Client("user_bot", api_id=api_id, api_hash=api_hash) as client:
        await fetch_new_messages(client)

if __name__ == "__main__":
    asyncio.run(main())
