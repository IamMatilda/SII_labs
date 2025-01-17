# Импортируем необходимые библиотеки
from transformers import BertTokenizer, BertForSequenceClassification
import torch
import matplotlib.pyplot as plt
from datetime import datetime
from db_operations import fetch_messages  # Импортируем метод для получения данных из базы данных
from collections import defaultdict

# Шаг 1. Получение данных из базы данных
# Получаем данные
data = fetch_messages(limit=300)

# Проверка возвращаемых данных
if not data:
    print("fetch_messages вернула пустой список.")
    exit()

print(f"Пример первых 5 сообщений из fetch_messages:")
for idx, item in enumerate(data[:5], 1):
    print(f"{idx}. Текст: {item['text']}, Дата: {item['date']}")

# Фильтрация пустых или некорректных текстов
data = [item for item in data if item["text"] and item["text"].strip()]
if not data:
    print("Все сообщения пустые или некорректные после фильтрации.")
    exit()

print(f"Сообщения для анализа: {len(data)}")

# Шаг 2. Анализ тональности сообщений
# Загружаем модель и токенизатор BERT для анализа тональности
tokenizer = BertTokenizer.from_pretrained('nlptown/bert-base-multilingual-uncased-sentiment')
model = BertForSequenceClassification.from_pretrained('nlptown/bert-base-multilingual-uncased-sentiment')

# Токенизация сообщений
texts = [item["text"] for item in data]
encoded_inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")

# Анализ тональности с помощью модели
with torch.no_grad():
    outputs = model(**encoded_inputs)

# Определяем метки тональности
labels = ['очень негативная', 'негативная', 'нейтральная', 'позитивная', 'очень позитивная']
predictions = torch.argmax(outputs.logits, dim=-1)

# Добавляем тональность к сообщениям
for i, item in enumerate(data):
    item["sentiment"] = labels[predictions[i]]
    item["sentiment_score"] = predictions[i].item()  # Сохраняем числовой результат для графика

# Шаг 3. Группировка сообщений по user_id
grouped_data = defaultdict(list)
for item in data:
    grouped_data[item["user_id"]].append(item)

# Шаг 4. Построение графиков для каждого пользователя
for user_id, messages in grouped_data.items():
    # Преобразуем время и тональность
    time_points = [item["date"] for item in messages]
    sentiment_scores = [item["sentiment_score"] for item in messages]

    # Построение графика
    plt.figure(figsize=(12, 6))
    plt.plot(time_points, sentiment_scores, marker='o', color='b', label='Тональность')
    plt.xticks(rotation=45)
    plt.yticks(range(len(labels)), labels)
    plt.xlabel("Время")
    plt.ylabel("Тональность")
    plt.title(f"Изменение настроения пользователя {user_id}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Шаг 5. Вывод отчета
print("Отчет об изменении настроения:")
for item in data:
    print(f"Время: {item['date']}, Сообщение: \"{item['text']}\", Тональность: {item['sentiment']}")
