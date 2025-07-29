
import uuid
import requests
from config import YOOKASSA_API_KEY, YOOKASSA_SHOP_ID, DOMAIN, YOOMONEY_WALLET
from database import update_subscription, get_all_users, remove_premium, add_videos, add_payment, get_payments_stats
import re
import os
from functools import wraps
from flask import Flask, request, Response
from loguru import logger
from service import grant_videos, set_premium
from data import add_payment, get_all_users, remove_premium
from external_api import create_yookassa_payment, create_yoomoney_payment

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

app = Flask(__name__)
logger.add("payment.log", rotation="10 MB")

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "password")

def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS

def authenticate():
    return Response(
        'Требуется авторизация', 401,
        {'WWW-Authenticate': 'Basic realm="Admin Area"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route("/webhook", methods=["POST"])
@requires_auth
def webhook():
    logger.info(f"Webhook received: {request.json}")
    try:
        payload = request.json
        if payload["event"] == "payment.succeeded":
            telegram_id = int(payload["object"]["description"].split()[-1])
            amount = int(float(payload["object"]["amount"]["value"]))
            tariff = get_tariff_by_price(amount)
            add_payment(telegram_id, amount, "yookassa", "success")
            if tariff:
                grant_videos(telegram_id, tariff["count"])
                logger.info(f"Videos granted: {telegram_id}, {tariff['count']}")
            else:
                set_premium(telegram_id)
                logger.info(f"Subscription updated: {telegram_id}")
        return "OK", 200
    except Exception as e:
        logger.exception(f"Webhook error: {e}")
        return "ERROR", 500

@app.route("/admin", methods=["GET"])
@requires_auth
def admin_panel():
    users = get_all_users()
    stats = get_payments_stats()
    html = "<h1>Пользователи</h1><table border=1><tr><th>ID</th><th>Премиум</th><th>Истекает</th><th>Действия</th></tr>"
    for u in users:
        html += f"<tr><td>{u['telegram_id']}</td><td>{'Да' if u['is_premium'] else 'Нет'}</td><td>{u['expires_at'] or ''}</td>"
        if u['is_premium']:
            html += f"<td><form method='post' action='/admin/remove'><input type='hidden' name='id' value='{u['telegram_id']}'><button type='submit'>Снять премиум</button></form></td>"
        else:
            html += f"<td><form method='post' action='/admin/give'><input type='hidden' name='id' value='{u['telegram_id']}'><button type='submit'>Выдать премиум</button></form></td>"
        html += "</tr>"
    html += "</table>"
    html += f"<h2>Статистика</h2><ul>"
    html += f"<li>Всего оплат: {stats['payments_count']}</li>"
    html += f"<li>Доход: {stats['total_income']} ₽</li>"
    html += f"<li>Уникальных пользователей: {stats['unique_users']}</li>"
    html += "</ul>"
    return html

@app.route("/admin/give", methods=["POST"])
@requires_auth
def admin_give():
    telegram_id = int(request.form['id'])
    set_premium(telegram_id)
    return "<p>Премиум выдан. <a href='/admin'>Назад</a></p>"

@app.route("/admin/remove", methods=["POST"])
@requires_auth
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
            amount = int(float(data.get("amount", 0)))
            tariff = get_tariff_by_price(amount)
            add_payment(telegram_id, amount, "yoomoney", "success")
            if tariff:
                grant_videos(telegram_id, tariff["count"])
                return "OK: videos granted", 200
    return "NO ACTION", 200
