
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from database import get_user, add_user, update_subscription, remove_premium, decrement_free_generation
from payment import create_payment, create_yoomoney_payment
from veo3_api import generate_with_veo3
from config import CHANNEL_USERNAME
from aiogram import Bot

router = Router()

TARIFFS = [
    {"count": 1, "price": 80},
    {"count": 2, "price": 150},
    {"count": 3, "price": 210},
    {"count": 4, "price": 270},
]

async def check_subscription(user_id, bot: Bot) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

@router.message(Command("start"))
async def start(message: Message):
    # Проверка подписки на канал
    if not await check_subscription(message.from_user.id, message.bot):
        link = f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
        await message.answer(f"Чтобы пользоваться ботом, подпишитесь на наш канал: {link}")
        return
    user = get_user(message.from_user.id)
    if not user:
        add_user(message.from_user.id)
    await message.answer("Привет! Чтобы использовать Veo3 Bot, купи премиум: /buy")

@router.message(Command("buy"))
async def buy(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=f"{t['count']} видео — {t['price']}₽")] for t in TARIFFS],
        resize_keyboard=True
    )
    await message.answer(
        "Выберите тариф (количество видео):",
        reply_markup=kb
    )

@router.message(lambda m: any(m.text and m.text.startswith(f"{t['count']} видео") for t in TARIFFS))
async def buy_tariff(message: Message):
    for t in TARIFFS:
        if message.text.startswith(f"{t['count']} видео"):
            payment_url = create_payment(t['price'], message.from_user.id)
            yoomoney_url = create_yoomoney_payment(t['price'], message.from_user.id)
            text = (
                f"Тариф: {t['count']} видео — {t['price']}₽\n"
                "Выберите способ оплаты:\n"
                f"1. ЮKassa (банковские карты, СБП): {payment_url}\n"
                f"2. YooMoney (кошелёк, P2P): {yoomoney_url}\n"
                "\nПосле оплаты вам будет начислено соответствующее количество видео."
            )
            await message.answer(text)
            break

@router.message(F.text)
async def handle_prompt(message: Message):
    # Проверка подписки на канал
    if not await check_subscription(message.from_user.id, message.bot):
        link = f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
        await message.answer(f"Чтобы пользоваться ботом, подпишитесь на наш канал: {link}")
        return
    user = get_user(message.from_user.id)
    if not user:
        add_user(message.from_user.id)
        user = get_user(message.from_user.id)
    # 1. Бесплатные генерации
    if not user["is_premium"]:
        if user["free_generations"] and user["free_generations"] > 0:
            decrement_free_generation(message.from_user.id)
            result_file = generate_with_veo3(message.text)
            with open(result_file, "rb") as video:
                await message.answer_video(video, caption=f"(Бесплатная генерация, осталось: {user['free_generations']-1})\nВаше видео готово! Видео хранится 2 дня.")
            return
        # 2. Оплаченные видео
        elif user["videos_left"] and user["videos_left"] > 0:
            from database import decrement_video
            decrement_video(message.from_user.id)
            result_file = generate_with_veo3(message.text)
            with open(result_file, "rb") as video:
                await message.answer_video(video, caption=f"(Оплаченное видео, осталось: {user['videos_left']-1})\nВаше видео готово! Видео хранится 2 дня.")
            return
        else:
            await message.answer("У вас закончились бесплатные и оплаченные видео. Купите ещё через /buy.")
            return
    # 3. Премиум
    from datetime import datetime
    if user["expires_at"]:
        expires = datetime.fromisoformat(user["expires_at"])
        if expires < datetime.now():
            remove_premium(message.from_user.id)
            await message.answer("Срок вашей подписки истёк. Купите видео через /buy.")
            return
    result_file = generate_with_veo3(message.text)
    with open(result_file, "rb") as video:
        await message.answer_video(video, caption="Ваше видео готово! Видео хранится 2 дня.")
