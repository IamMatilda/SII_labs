Анализ личного Telegram-канала c использованием трансформеров, определением состояния, достижений и рекомендациями контента


Описание задачи


1)Проведение анализа личного Telegaram-канала

2)Определение ключевых тем, настроения и достижений.

3)Генерация рекомендаций и формирование отчётов.


Описание проекта:


Основные компоненты системы:


Модуль сбора данных из Telegram-канала:


Задача: Автоматический сбор всех сообщений и медиафайлов из личного Telegram-канала.

Решение: Использование Telegram API для доступа к данным канала и их загрузки в базу данных для дальнейшего анализа.


Система анализа состояния и достижений:


Задача: Анализ текстовых сообщений для выявления эмоционального состояния автора, ключевых достижений и изменений настроения в разные периоды.

Решение: Применение NLP моделей для анализа тональности, выявления эмоциональных паттернов и фиксации важных событий.


Модуль генерации воспоминаний:


Задача: Создание текстовых и визуальных воспоминаний на основе достижений и значимых моментов, зафиксированных в Telegram-канале.

Решение: Использование моделей для генерации кратких текстов и создания простых визуальных представлений воспоминаний.


Рекомендательная система контента:


Задача: Предоставление персонализированных рекомендаций по контенту (статьи, музыка, фильмы) на основе анализа состояния автора.

Решение: Использование комбинированной модели рекомендаций, основанной на данных из Telegram-канала и анализе текущего эмоционального состояния.


Технологический стек:


Обработка текста: BERT, RoBERTa (Hugging Face OSS 2024),BART.

Интеграция с Telegram API: python-telegram-bot, Telethon.

Рекомендательные модели: Коллаборативная и контентная фильтрация.

Визуализация и создание воспоминаний: Matplotlib.

Хранение данных: PostgreSQL.


ИНСТРУКЦИЯ ПО ЗАПУСКУ


Для запуска необходимо иметь следующее ПО: Docker, PyCharm с python

1)Необходимо открыть Docker

2)После клонирования проекта, необходимо открыть проект через Pycharm, запустить docker-compose.yml (при необходимости, можно поменять название и пароль БД)*
*если данные будут изменены, то их нужно будет поменять в файле db_config.py

3)После запуска файла, убедиться, что был запущен контейнер с соответствующим названием 

4)При необходимости, можно подключиться к БД через Pycharm, используя инструмент Database, введя данные из docker-compose.yml или db_config.py

5)В файле config.ini необходимо указать свои данные Telegram API

6)В файле last_message_id.txt поменять значение на 1

7)В файле telegram_parser.py в 32 строке необходимо указать адрес канала для парсинга

8)После этого, можно запускать main.py для парсинга данных


После успешного парсинга можно выполнять операции над данными


1)Запуск mood_in_time.py строит график состояния во впремени

2)Запуск achievement.py показывает достижения во времени

3)Запуск memories_and_recomendations.py выводит воспоминания и рекомендации

