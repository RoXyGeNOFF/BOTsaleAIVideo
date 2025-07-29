import time
from google import genai
from config import VEO3_API_KEY, YOOKASSA_API_KEY, YOOKASSA_SHOP_ID, DOMAIN, YOOMONEY_WALLET
import requests
import uuid

def generate_video_with_veo3(prompt: str) -> str:
    client = genai.Client(api_key=VEO3_API_KEY)
    operation = client.models.generate_videos(
        model="veo-3.0-generate-preview",
        prompt=prompt,
    )
    while not operation.done:
        time.sleep(10)
        operation = client.operations.get(operation)
    video_bytes = operation.response.video
    filename = f"output_{int(time.time())}.mp4"
    with open(filename, "wb") as f:
        f.write(video_bytes)
    return filename

def create_yookassa_payment(amount_rub: int, telegram_id: int) -> str:
    idempotence_key = str(uuid.uuid4())
    headers = {"Idempotence-Key": idempotence_key}
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
    return f"https://yoomoney.ru/to/{YOOMONEY_WALLET}?amount={amount_rub}&label=veo3_{telegram_id}" 