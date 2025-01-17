from db.db_connection import get_connection
from psycopg2.extras import execute_values
import re
import psycopg2
from psycopg2 import extras


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


def fetch_messages(limit=300):
    """
    Получение сообщений из таблицы Message с поддержкой RealDictRow.
    """
    conn = get_connection()
    if not conn:
        print("Не удалось установить соединение с базой данных.")
        return []

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)  # Используем RealDictCursor

        # SQL-запрос
        query = f'SELECT text, date FROM "Message" ORDER BY date DESC LIMIT %s'
        cursor.execute(query, (limit,))
        messages = cursor.fetchall()

        # Отладочный вывод
        print("Сырые данные из базы данных:")
        print(messages)

        if not messages:
            print("Нет сообщений для получения.")
            return []

        # Преобразование данных в список словарей
        result = []
        for row in messages:
            text = row.get("text")
            date = row.get("date")
            if text and text.strip() and date:
                result.append({"text": text.strip(), "date": date})

        if not result:
            print("После фильтрации сообщений не осталось.")
            return []

        print(f"Сообщений для анализа: {len(result)}")
        return result

    except Exception as e:
        print(f"Ошибка при получении сообщений: {e.__class__.__name__}: {e}")
        return []
    finally:
        try:
            cursor.close()
        except Exception as e:
            print(f"Ошибка при закрытии курсора: {e.__class__.__name__}: {e}")
        try:
            conn.close()
        except Exception as e:
            print(f"Ошибка при закрытии соединения: {e.__class__.__name__}: {e}")

def fetch_analytics(limit=300):
    """
    Получение аналитических данных из таблицы Massage Analytic.
    """
    conn = get_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        query = f'''
            SELECT text_cleaned, message_id
            FROM "MassageAnalytic"
            ORDER BY message_id DESC
            LIMIT {300}
        '''
        cursor.execute(query)
        analytics = cursor.fetchall()
        return [{"cleaned_text": row[0], "message_id": row[1]} for row in analytics]
    except Exception as e:
        print(f"Ошибка при получении аналитических данных: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def fetch_users(limit=10):
    """
    Получение данных пользователей из таблицы User.
    """
    conn = get_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        query = f'SELECT id FROM "User" ORDER BY id LIMIT {10}'
        cursor.execute(query)
        users = cursor.fetchall()
        return [{"user_id": row[0]} for row in users]
    except Exception as e:
        print(f"Ошибка при получении пользователей: {e}")
        return []
    finally:
        cursor.close()
        conn.close()