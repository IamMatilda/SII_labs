from transformers import BertTokenizer, BertForSequenceClassification
import torch
from collections import defaultdict
from db_operations import fetch_messages

# Шаг 1. Получение данных из базы данных
data = fetch_messages(limit=300)
# Проверка возвращаемых данных
if not data:
    print("fetch_messages вернула пустой список.")
    exit()

print(f"Пример первых 5 сообщений из fetch_messages:")
for idx, item in enumerate(data[:5], 1):
    print(f"{idx}. Текст: {item['text']}, Дата: {item['date']}, Пользователь: {item['user_id']}")

# Фильтрация пустых или некорректных текстов
data = [item for item in data if item["text"] and item["text"].strip()]
if not data:
    print("Все сообщения пустые или некорректные после фильтрации.")
    exit()

print(f"Сообщения для анализа: {len(data)}")

# Шаг 2. Группировка сообщений по пользователям
grouped_data = defaultdict(list)
for item in data:
    grouped_data[item["user_id"]].append(item)

# Шаг 3. Загрузка модели для классификации достижений
# Используем предобученную модель BERT
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

# Предположим, что метка 0 — "не достижение", а 1 — "достижение"
# Шаг 4. Анализ сообщений для каждого пользователя
results = {}

for user_id, messages in grouped_data.items():
    print(f"Анализ для пользователя: {user_id}")

    # Токенизация сообщений пользователя
    texts = [item["text"] for item in messages]
    encoded_inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")

    # Анализ с использованием модели
    with torch.no_grad():
        outputs = model(**encoded_inputs)

    # Прогнозируем вероятности
    probabilities = torch.softmax(outputs.logits, dim=-1)
    print("Вероятности:", probabilities)

    # Прогнозируем метки с порогом
    threshold = 0.6 # Настраиваемый порог
    predictions = (probabilities[:, 1] > threshold).int()  # Вероятность метки 1 > порога

    # Добавляем результаты анализа к сообщениям
    for i, item in enumerate(messages):
        item["achievement"] = "достижение" if predictions[i].item() == 1 else "не достижение"

    # Отбор только значимых достижений для пользователя
    achievements = [item for item in messages if item["achievement"] == "достижение"]

    # Сохраняем результат анализа для данного пользователя
    results[user_id] = achievements

# Шаг 5. Вывод отчета
print("Отчет о значимых достижениях для каждого пользователя:")
for user_id, achievements in results.items():
    print(f"\nПользователь {user_id}:")
    if achievements:
        for item in achievements:
            print(f"  Время: {item['date']}, Сообщение: \"{item['text']}\", Тип: {item['achievement']}")
    else:
        print("  Нет значимых достижений.")
