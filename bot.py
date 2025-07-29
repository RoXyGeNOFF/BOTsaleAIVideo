
import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router
from database import init_db
from database import get_users_with_expiring_premium

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

dp.include_router(router)

async def notify_expiring_premium(bot: Bot):
    while True:
        users = get_users_with_expiring_premium()
        for user_id in users:
            try:
                await bot.send_message(user_id, "Ваша премиум-подписка истекает через 3 дня! Продлите её, чтобы не потерять доступ.")
            except Exception:
                pass
        await asyncio.sleep(24 * 60 * 60)  # Проверять раз в сутки

async def main():
    init_db()
    asyncio.create_task(notify_expiring_premium(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
