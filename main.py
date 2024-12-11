from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import Message
import asyncio
import logging
import os

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Создаем роутер для обработки сообщений
router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.chat.type == "private":
        await message.answer(
            "Привет! Я эхо-бот. Отправь мне любое сообщение, и я его повторю."
        )

# Обработчик всех остальных текстовых сообщений
@router.message()
async def echo_message(message: Message):
    if message.chat.type == "private":
        # Повторяем текст сообщения пользователя
        await message.answer(message.text)

# Функция настройки и запуска бота
async def main():
    # Создаем объект бота (токен получаем от @BotFather в Telegram)
    bot = Bot(token=os.getenv("TG_TOKEN"))
    
    # Создаем диспетчер
    dp = Dispatcher()
    
    # Регистрируем роутер
    dp.include_router(router)
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запускаем основную функцию
    asyncio.run(main())
