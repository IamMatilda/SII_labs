from collections import Counter
import matplotlib.pyplot as plt
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from db_operations import fetch_messages  # Импортируем метод для получения данных из базы данных
import os

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Загрузка стоп-слов (для русского языка)
nltk.download('punkt')
nltk.download('stopwords')
stop_words = set(stopwords.words('russian'))

# Дополнительные стоп-слова
additional_stopwords = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "да", "так", "вот", "но", "для", "же", "ты", "бы", "по", "только", "ее", "мне", "у", "от", "из", "мы", "вы", "их", "это", "к", "всех", "весь", "еще", "даже", "если", "при", "меня", "о", "такой", "сам", "будет", "без", "или", "всю", "она", "кто", "тот", "этот", "мочь", "ничего", "эти", "этого", "мои", "теперь", "когда", "куда", "между", "другие", "вас", "тоже", "также"
}
stop_words.update(additional_stopwords)

# Функция для очистки текста
def clean_message(message):
    message = re.sub(r'[^\w\s]', '', message)
    message = message.lower()
    words = word_tokenize(message)
    filtered_words = [word for word in words if word not in stop_words]
    return " ".join(filtered_words)

# Получение данных из базы данных
messages_data = fetch_messages(limit=15)
if not messages_data:
    print("Нет сообщений для обработки.")
    exit()

# Очистка сообщений
cleaned_messages = [clean_message(item["text"]) for item in messages_data]

# Загрузка модели и токенизатора GPT-2
model_name = "sberbank-ai/rugpt3small_based_on_gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)

# Анализ настроений
sentiment_analyzer = pipeline("sentiment-analysis", model="blanchefort/rubert-base-cased-sentiment")
sentiments = [sentiment_analyzer(msg)[0] for msg in cleaned_messages]

# Формирование контекста для генерации текста
context = "Воспоминания на основе данных:\n"
for i, (msg, sentiment) in enumerate(zip(cleaned_messages, sentiments)):
    context += f"{i + 1}. {msg} (Состояние: {sentiment['label']})\n"

# Генерация текста на основе контекста
input_ids = tokenizer.encode(context, return_tensors="pt")
output = model.generate(
    input_ids,
    max_length=800,
    temperature=0.8,
    top_p=0.85,
    repetition_penalty=1.2
)

generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
print("Сгенерированный текст с учетом настроений:\n", generated_text)

# Кластеризация сообщений
vectorizer = TfidfVectorizer(stop_words=None)
tfidf_matrix = vectorizer.fit_transform(cleaned_messages)
num_clusters = 3
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
labels = kmeans.fit_predict(tfidf_matrix)

# Группировка сообщений по кластерам
clustered_messages = {i: [] for i in range(num_clusters)}
for idx, label in enumerate(labels):
    clustered_messages[label].append(messages_data[idx]["text"])

print("\nКластеры сообщений:")
for cluster, msgs in clustered_messages.items():
    print(f"Кластер {cluster}: {msgs}")

# Генерация рекомендаций на основе кластеров
topic_mapping = {
    "спорт": ["спорт", "игра", "команда", "победа"],
    "политика": ["политика", "власть", "новости", "государство"],
    "финансы": ["деньги", "акции", "доллар", "экономика"],
    "путешествия": ["отдых", "путешествия", "аквапарк", "турция"],
    "здоровье": ["здоровье", "головная", "таблетки"]
}

recommendations = set()
for cluster, msgs in clustered_messages.items():
    for msg in msgs:
        for topic, words in topic_mapping.items():
            if any(word in msg.lower() for word in words):
                recommendations.add(topic)

print("\nРекомендации на основе кластеров:")
print(list(recommendations))

# Сбор обратной связи
feedback = {"positive": [], "negative": []}
print("\nОцените рекомендации:")
for rec in recommendations:
    print(f"Рекомендация: {rec}")
    user_input = input("Оцените (👍 или 👎): ")
    if user_input == "👍":
        feedback["positive"].append(rec)
    elif user_input == "👎":
        feedback["negative"].append(rec)

print("\nСобранная обратная связь:")
print("👍 Понравилось:", feedback["positive"])
print("👎 Не понравилось:", feedback["negative"])

# Обновление приоритетов на основе обратной связи
preferences = {topic: 1 for topic in topic_mapping.keys()}
for rec in feedback["positive"]:
    preferences[rec] += 1
for rec in feedback["negative"]:
    preferences[rec] -= 1

# Генерация новых рекомендаций с учетом обратной связи
new_recommendations = [
    (f"Рекомендуем вам больше узнать про {topic}.", preferences[topic])
    for topic in preferences
]
sorted_recommendations = sorted(new_recommendations, key=lambda x: x[1], reverse=True)

print("\nНовые рекомендации:")
for rec, weight in sorted_recommendations:
    print(f"{rec} (вес: {weight})")