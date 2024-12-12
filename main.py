from aiogram import Bot, Dispatcher
import asyncio
import logging
import os

from handlers import router

logging.basicConfig(level=logging.INFO)

if os.getenv("SERVER") == "production":
    TOKEN = os.getenv("TG_TOKEN")
else:
    from temp.config import DEV_BOT_TOKEN

    TOKEN = DEV_BOT_TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(router)


async def main():
    # Запуск бота
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
