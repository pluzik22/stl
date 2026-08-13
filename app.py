from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Ссылку вебхука будем хранить в переменной окружения (не в коде!)
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


@app.route("/")
def home():
    return (
        "Бот работает. Чтобы отправить сообщение в Discord, открой:<br>"
        "<code>/send?text=твой текст</code>"
    )


@app.route("/send", methods=["GET", "POST"])
def send():
    text = request.values.get("text", "").strip()

    if not text:
        return {"error": "Не передан параметр text. Пример: /send?text=привет"}, 400

    if not WEBHOOK_URL:
        return {"error": "DISCORD_WEBHOOK_URL не настроен на сервере"}, 500

    response = requests.post(WEBHOOK_URL, json={"content": text})

    if response.status_code in (200, 204):
        return {"status": "ok", "sent": text}
    else:
        return {"error": "Discord отклонил запрос", "details": response.text}, 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
