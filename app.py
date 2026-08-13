import asyncio
import os
import threading

import discord
from flask import Flask, request

# ---------- Настройки ----------
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID")
CHANNEL_ID = int(CHANNEL_ID) if CHANNEL_ID else None

# ---------- Discord-бот ----------
intents = discord.Intents.default()
bot = discord.Client(intents=intents)

# Отдельный event loop для бота — крутится в фоновом потоке,
# пока Flask обрабатывает обычные HTTP-запросы
bot_loop = asyncio.new_event_loop()


@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")


def run_bot():
    asyncio.set_event_loop(bot_loop)
    bot_loop.run_until_complete(bot.start(BOT_TOKEN))


# ---------- Веб-сервер ----------
app = Flask(__name__)


@app.route("/")
def home():
    status = "подключен" if bot.is_ready() else "подключается..."
    return (
        f"Бот-статус: {status}<br>"
        "Чтобы отправить сообщение в Discord, открой:<br>"
        "<code>/send?text=твой текст</code>"
    )


@app.route("/send", methods=["GET", "POST"])
def send():
    text = request.values.get("text", "").strip()

    if not text:
        return {"error": "Не передан параметр text. Пример: /send?text=привет"}, 400

    if not CHANNEL_ID:
        return {"error": "DISCORD_CHANNEL_ID не настроен на сервере"}, 500

    if not bot.is_ready():
        return {"error": "Бот ещё подключается, попробуйте через пару секунд"}, 503

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        return {"error": "Канал не найден. Проверьте DISCORD_CHANNEL_ID и права бота"}, 500

    # Отправляем сообщение через event loop бота из потока Flask
    future = asyncio.run_coroutine_threadsafe(channel.send(text), bot_loop)
    try:
        future.result(timeout=10)
    except Exception as e:
        return {"error": "Не удалось отправить сообщение", "details": str(e)}, 502

    return {"status": "ok", "sent": text}


# ---------- Запуск ----------
# Поток с ботом запускаем сразу при импорте модуля (не только внутри
# __main__), потому что на хостинге сервер обычно запускается через
# gunicorn, который __main__ не выполняет.
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
