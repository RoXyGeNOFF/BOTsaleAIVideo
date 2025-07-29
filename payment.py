
import uuid
import requests
from config import YOOKASSA_API_KEY, YOOKASSA_SHOP_ID, DOMAIN, YOOMONEY_WALLET
from database import update_subscription, get_all_users, remove_premium, add_videos
import re

TARIFFS = [
    {"count": 1, "price": 80},
    {"count": 2, "price": 150},
    {"count": 3, "price": 210},
    {"count": 4, "price": 270},
]

def get_tariff_by_price(price):
    for t in TARIFFS:
        if t["price"] == price:
            return t
    return None

def create_payment(amount_rub: int, telegram_id: int) -> str:
    idempotence_key = str(uuid.uuid4())
    headers = {
        "Idempotence-Key": idempotence_key
    }
    auth = (YOOKASSA_SHOP_ID, YOOKASSA_API_KEY)

    payload = {
        "amount": {"value": str(amount_rub), "currency": "RUB"},
        "confirmation": {
            "type": "redirect",
            "return_url": f"{DOMAIN}/success/{telegram_id}"
        },
        "capture": True,
        "description": f"Premium подписка для {telegram_id}"
    }

    response = requests.post(
        "https://api.yookassa.ru/v3/payments",
        json=payload,
        headers=headers,
        auth=auth
    )
    data = response.json()
    return data["confirmation"]["confirmation_url"]

def create_yoomoney_payment(amount_rub: int, telegram_id: int) -> str:
    # Генерация P2P-ссылки на оплату через YooMoney
    return f"https://yoomoney.ru/to/{YOOMONEY_WALLET}?amount={amount_rub}&label=veo3_{telegram_id}"

from flask import Flask, request

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.json
    if payload["event"] == "payment.succeeded":
        telegram_id = int(payload["object"]["description"].split()[-1])
        amount = int(float(payload["object"]["amount"]["value"]))
        tariff = get_tariff_by_price(amount)
        if tariff:
            add_videos(telegram_id, tariff["count"])
        else:
            update_subscription(telegram_id)  # fallback: если старый тариф
    return "OK", 200

@app.route("/admin", methods=["GET"])
def admin_panel():
    users = get_all_users()
    html = "<h1>Пользователи</h1><table border=1><tr><th>ID</th><th>Премиум</th><th>Истекает</th><th>Действия</th></tr>"
    for u in users:
        html += f"<tr><td>{u['telegram_id']}</td><td>{'Да' if u['is_premium'] else 'Нет'}</td><td>{u['expires_at'] or ''}</td>"
        if u['is_premium']:
            html += f"<td><form method='post' action='/admin/remove'><input type='hidden' name='id' value='{u['telegram_id']}'><button type='submit'>Снять премиум</button></form></td>"
        else:
            html += f"<td><form method='post' action='/admin/give'><input type='hidden' name='id' value='{u['telegram_id']}'><button type='submit'>Выдать премиум</button></form></td>"
        html += "</tr>"
    html += "</table>"
    return html

@app.route("/admin/give", methods=["POST"])
def admin_give():
    telegram_id = int(request.form['id'])
    update_subscription(telegram_id)
    return "<p>Премиум выдан. <a href='/admin'>Назад</a></p>"

@app.route("/admin/remove", methods=["POST"])
def admin_remove():
    telegram_id = int(request.form['id'])
    remove_premium(telegram_id)
    return "<p>Премиум снят. <a href='/admin'>Назад</a></p>"

@app.route("/yoomoney_webhook", methods=["POST"])
def yoomoney_webhook():
    data = request.form or request.json
    label = data.get("label")
    success = str(data.get("unaccepted", "0")) == "0" and str(data.get("operation_id"))
    if label and label.startswith("veo3_") and success:
        import re
        match = re.match(r"veo3_(\d+)", label)
        if match:
            telegram_id = int(match.group(1))
            # Определяем тариф по сумме
            amount = int(float(data.get("amount", 0)))
            tariff = get_tariff_by_price(amount)
            if tariff:
                add_videos(telegram_id, tariff["count"])
                return "OK: videos granted", 200
    return "NO ACTION", 200
