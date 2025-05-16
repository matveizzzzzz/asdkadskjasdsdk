import telebot
import sqlite3
import uuid
import json
import asyncio
import websockets
from telebot import types
import csv
import random
from deep_translator import GoogleTranslator


API_TOKEN = '7955363428:AAETEug-nrrOVhyZMJXSbl61lGFSpBE9giU'
a = 'nRRsqiRDM1W2Avir7EI3qpIy4XkPxjPY'
ADMIN_ID = 7940544491
GENERATION_PRICE = 50

bot = telebot.TeleBot(API_TOKEN)

# Инициализация базы данных

def init_db():
    conn = sqlite3.connect('useras.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            user_id INTEGER,
            generations_left INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Функции работы с БД

def register_user(username, user_id):
    conn = sqlite3.connect('useras.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT OR IGNORE INTO users (username, user_id) VALUES (?, ?)''', (username, user_id))
    conn.commit()
    conn.close()

def get_generations_left(username):
    conn = sqlite3.connect('useras.db')
    cursor = conn.cursor()
    cursor.execute('SELECT generations_left FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def decrement_generation(username):
    conn = sqlite3.connect('useras.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET generations_left = generations_left - 1 WHERE username = ? AND generations_left > 0''', (username,))
    conn.commit()
    conn.close()

def add_generations(username, count):
    conn = sqlite3.connect('useras.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET generations_left = generations_left + ? WHERE username = ?''', (count, username))
    conn.commit()
    conn.close()

# Получение рандомной музыки

import os  # в начале файла, если не добавлен

def get_random_music_file():
    try:
        with open('music.csv', newline='', encoding='utf-8') as csvfile:
            reader = list(csv.DictReader(csvfile))
            if not reader:
                return None, None
            track = random.choice(reader)
            path = os.path.join("music", track['path'])  # путь внутри папки music
            return track['title'], path
    except:
        return None, None




# Генерация изображения через WebSocket

async def create_image(prompt):
    async with websockets.connect('wss://ws-api.runware.ai/v1') as websocket:
        await websocket.send(json.dumps([{"taskType": "authentication", "apiKey": a}]))
        await websocket.recv()

        request = [{
            "positivePrompt": prompt,
            "model": "runware:100@1",
            "steps": 4,
            "width": 512,
            "height": 512,
            "numberResults": 1,
            "outputType": ["URL"],
            "taskType": "imageInference",
            "taskUUID": uuid.uuid4().hex
        }]

        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        return json.loads(response)['data'][0]['imageURL']

# Обработчики команд

@bot.message_handler(commands=['start'])
def handle_start(message):
    username = message.from_user.username or f"id_{message.from_user.id}"
    register_user(username, message.from_user.id)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎨 Генерация", "💎 Покупка")
    markup.row("ℹ️ Информация", "🎵 Рандомная музыка", "💰 Баланс")

    try:
        with open("welcome.jpg", "rb") as photo:
            bot.send_photo(
                message.chat.id,
                photo,
                caption="👋 Добро пожаловать! Я бот для генерации изображений с помощью ИИ.\n\n"
                        "Выбери действие из меню ниже:"
            )
    except FileNotFoundError:
        bot.send_message(message.chat.id, "(файл welcome.jpg не найден на сервере)")

    # Отправляем клавиатуру (если надо отдельно)
    bot.send_message(
        message.chat.id,
        "👇 Выбери действие из меню:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def check_balance(message):
    username = message.from_user.username or f"id_{message.from_user.id}"
    register_user(username, message.from_user.id)
    balance = get_generations_left(username)
    bot.send_message(
        message.chat.id,
        f"💰 <b>Твой баланс:</b> {balance} генераций\n\n"
        "Чтобы получить больше генераций, нажми кнопку '💎 Покупка'",
        parse_mode='HTML'
    )

@bot.message_handler(func=lambda m: m.text == "🎨 Генерация")
def menu_generate(message):
    username = message.from_user.username or f"id_{message.from_user.id}"
    register_user(username, message.from_user.id)
    try:
        with open("welcomee.jpg", "rb") as photo:
            bot.send_photo(
                message.chat.id,
                photo,
                caption=
        "🖌️ <b>Генерация изображения</b>\n\n"
        "Пришли мне текст на любом языке - я переведу его на английский и создам уникальное изображение.\n\n"
        "<i>Примеры хороших промптов:</i>\n"
        "• Красивая девушка в стиле аниме\n"
        "• Фэнтезийный замок на горе, цифровая живопись\n"
        "• Космический корабль в стиле киберпанк",
        parse_mode='HTML'
    )
    except FileNotFoundError:
        bot.send_message(message.chat.id, "Привет! (файл welcome.jpg не найден на сервере)")

@bot.message_handler(func=lambda m: m.text == "💎 Покупка")
def menu_purchase(message):
    username = message.from_user.username or f"id_{message.from_user.id}"
    register_user(username, message.from_user.id)
    bot.send_message(
        message.chat.id,
        f"💎 <b>Покупка генераций</b>\n\n"
        f"10 генераций = {GENERATION_PRICE}₽\n\n"
        "Чтобы купить, напиши админу: @isntmiller\n\n"
        "<i>После оплаты генерации будут добавлены вручную в течение 5 минут.</i>",
        parse_mode='HTML'
    )

@bot.message_handler(func=lambda message: message.text == "ℹ️ Информация")
def menu_info(message):
    username = message.from_user.username or f"id_{message.from_user.id}"
    register_user(username, message.from_user.id)
    balance = get_generations_left(username)
    text = (
        "👋 *Привет! Вот вся информация обо мне:*\n\n"
        "🤖 Я — бот генерации изображений с помощью нейросетей\n"
        "✏️ Просто введи текст на любом языке — и получишь уникальную картинку\n"
        "⚡ Генерация занимает всего пару секунд\n"
        "🎨 Поддерживаются любые стили: реализм, аниме, фэнтези и другие\n"
        "📥 Музыку для вдохновения можно получить прямо здесь — просто нажми 'Рандомная музыка'\n"
        "💎 Каждому пользователю даются лимиты генераций\n"
        f"📊 *У тебя осталось*: {balance} генераций\n"
        "🛍️ Хочешь больше? Купи 10 генераций всего за 50₽ (через 'Покупка')\n"
        "👨‍💼 Связь с админом: @isntmiller\n"
        "⚙️ Технологии: WebSocket + Runware AI\n"
        "🧠 В основе лежит мощная нейросеть для творчества\n"
        "📚 Все данные хранятся в безопасной базе\n"
        "🔒 Мы не передаём личные данные\n"
        "🙏 Спасибо, что пользуешься ботом!"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.text == "🎵 Рандомная музыка")
def menu_music(message):
    username = message.from_user.username or f"id_{message.from_user.id}"
    register_user(username, message.from_user.id)
    title, filepath = get_random_music_file()
    print(f"[DEBUG] Trying to open file: {filepath}")  # ← вот это добавь
    if title and filepath:
        try:
            with open(filepath, 'rb') as audio:
                bot.send_audio(message.chat.id, audio, caption=f"🎵 {title}")
        except FileNotFoundError:
            bot.send_message(message.chat.id,"Файл не найден на сервере.")
    else:
        bot.send_message(message.chat.id,
                         "😢 Не удалось отправить трек. Попробуйте позже.")


@bot.message_handler(commands=['add'])
def handle_add(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "Нет доступа.")
    try:
        _, username, count = message.text.split()
        add_generations(username, int(count))
        bot.send_message(message.chat.id,
                         f"✅ Пользователю {username} добавлено {count} генераций")
    except:
        bot.send_message(message.chat.id,
                         "❌ Ошибка. Формат: /add username количество")

@bot.message_handler(func=lambda m: True)
def handle_prompt(message):
    username = message.from_user.username or f"id_{message.from_user.id}"
    register_user(username, message.from_user.id)
    if get_generations_left(username) <= 0:
        return bot.send_message(
            message.chat.id,
            "😢 У вас закончились генерации.\n\n"
            "Чтобы получить больше, нажмите кнопку '💎 Покупка'")

    prompt = message.text
    translated_prompt = GoogleTranslator(source='auto', target='en').translate(prompt)


    prompt = message.text
    if len(prompt) > 500:
        return bot.send_message(
            message.chat.id,
            "❌ Слишком длинный промпт. Максимум 500 символов.")

    msg = bot.send_message(
        message.chat.id,
        f"🔄 Генерация изображения по запросу:\n\n<i>{prompt}</i>\n\n"
        "Пожалуйста, подождите 10-20 секунд...",
        parse_mode='HTML'
    )

    async def process():
        try:
            image_url = await create_image(translated_prompt)
            decrement_generation(username)
            bot.send_photo(message.chat.id, image_url,
                           caption=f"🎨 Результат:\n\n{prompt}",)
            bot.delete_message(message.chat.id, msg.message_id)
        except Exception as e:
            bot.send_message(
                message.chat.id,
                "❌ Ошибка при обработке вашего запроса. Попробуйте позже."
            )

    asyncio.run(process())

if __name__ == '__main__':
    bot.infinity_polling()
