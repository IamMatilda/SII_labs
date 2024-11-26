from db.db_connection import get_connection
from psycopg2.extras import execute_values
import re



def normalize_text(text):
    """
    Нормализация текста: удаление спецсимволов, ссылок и лишних пробелов.
    """
    if text is None:  # Если текст отсутствует, вернуть пустую строку
        return ""
    text = re.sub(r'http\S+|www\S+', '', text)  # Убираем ссылки
    text = text.strip()  # Убираем лишние пробелы
    return text


def insert_data(messages):
    """
    Запись данных в таблицы User, Message и Massage Analytic.
    """
    conn = get_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Нормализация текста и подготовка данных
        for msg in messages:
            msg["cleaned_text"] = normalize_text(msg["text"])

        # Запись данных в таблицу User
        user_data = {(msg["user_id"],) for msg in messages if "user_id" in msg and msg["user_id"]}
        user_query = 'INSERT INTO "User" (id) VALUES %s ON CONFLICT DO NOTHING'
        execute_values(cursor, user_query, user_data)

        # Запись данных в таблицу Message
        message_data = [
            (msg["text"], msg["date"], msg["user_id"])
            for msg in messages if "text" in msg and "date" in msg and "user_id" in msg
        ]
        message_query = 'INSERT INTO "Message" (text, date, user_id) VALUES %s'
        execute_values(cursor, message_query, message_data)

        # Запись данных в таблицу Massage Analytic
        analytic_data = [
            (msg["cleaned_text"], msg["user_id"])
            for msg in messages if "cleaned_text" in msg and "user_id" in msg
        ]
        analytic_query = 'INSERT INTO "MassageAnalytic" (text_cleaned, message_id) VALUES %s'
        execute_values(cursor, analytic_query, analytic_data)

        conn.commit()
        print("Данные успешно записаны в базу данных!")
    except Exception as e:
        print(f"Ошибка при записи в базу данных: {e}")
    finally:
        cursor.close()
        conn.close()
