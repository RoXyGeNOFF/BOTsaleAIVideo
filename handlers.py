
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from service import grant_videos, decrement_free_generation, set_premium, remove_premium, get_expiring_premium_users
from external_api import generate_video_with_veo3, create_yookassa_payment, create_yoomoney_payment
from veo3_api import generate_with_veo3_task
from config import CHANNEL_USERNAME
from aiogram import Bot
import asyncio

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

async def send_video_when_ready(bot: Bot, user_id: int, prompt: str, free: bool, left: int):
    task = generate_with_veo3_task.delay(prompt)
    progress_msg = await bot.send_message(user_id, "Генерация видео... [░░░░░░░░░░] 0%", reply_markup=ReplyKeyboardRemove())
    progress = 0
    while not task.ready():
        await asyncio.sleep(5)
        progress = min(progress + 20, 90)
        bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
        try:
            await bot.edit_message_text(f"Генерация видео... [{bar}] {progress}%", user_id, progress_msg.message_id)
        except Exception:
            pass
    result_file = task.get()
    caption = f"({'Бесплатная' if free else 'Оплаченная'} генерация, осталось: {left})\nВаше видео готово! Видео хранится 2 дня."
    with open(result_file, "rb") as video:
        await bot.send_video(user_id, video, caption=caption)
    try:
        await bot.edit_message_text("Видео готово!", user_id, progress_msg.message_id)
    except Exception:
        pass

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

@router.message(Command("faq"))
async def faq(message: Message):
    await message.answer(FAQ_TEXT, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

@router.message(Command("support"))
async def support(message: Message):
    await message.answer(SUPPORT_TEXT, reply_markup=ReplyKeyboardRemove())

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
            await message.answer("Ваше видео поставлено в очередь. Когда оно будет готово, вы получите уведомление!")
            asyncio.create_task(send_video_when_ready(message.bot, message.from_user.id, message.text, True, user['free_generations']-1))
            return
        # 2. Оплаченные видео
        elif user["videos_left"] and user["videos_left"] > 0:
            from database import decrement_video
            decrement_video(message.from_user.id)
            await message.answer("Ваше видео поставлено в очередь. Когда оно будет готово, вы получите уведомление!")
            asyncio.create_task(send_video_when_ready(message.bot, message.from_user.id, message.text, False, user['videos_left']-1))
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
    await message.answer("Ваше видео поставлено в очередь. Когда оно будет готово, вы получите уведомление!")
    asyncio.create_task(send_video_when_ready(message.bot, message.from_user.id, message.text, False, 0))
