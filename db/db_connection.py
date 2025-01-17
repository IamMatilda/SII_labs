from psycopg2.extras import RealDictCursor

from db.db_config import DB_CONFIG
import psycopg2


def get_connection():
    """
    Устанавливает соединение с базой данных.
    Возвращает объект подключения.
    """
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            port=DB_CONFIG["port"],
            cursor_factory=RealDictCursor,
        )
        return conn
    except Exception as e:
        print("Ошибка подключения к базе данных:", e)
        raise


def execute_query(query, params=None):
    """
    Выполняет SQL-запрос.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
    except Exception as e:
        print("Ошибка выполнения запроса:", e)
    finally:
        if conn:
            conn.close()
