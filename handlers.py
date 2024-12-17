import asyncio
import datetime
import logging
import os

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ChatJoinRequest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from messages import GIFT_MESSAGE
from utils import get_request, post_request

logger = logging.getLogger(__name__)

if os.getenv("SERVER") == "production":
    CHANNEL_ID = os.getenv("TG_CHANNEL_ID")
    BASE_URL = os.getenv("BASE_URL")
else:
    from temp import config

    CHANNEL_ID = config.DEV_CHANNEL_ID
    BASE_URL = config.BASE_URL

REFERRALS_URL = BASE_URL + "?query=/referrals"
GUESTS_URL = BASE_URL + "?query=/guests"

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Получить ссылку-приглашение", callback_data="create_invite")]
    ])

    await message.answer(
        "👋 Привет! Это бот для приглашения друзей в канал 'Как найти любимую работу | Skypro'\n\n"
        "Воспользуйтесь командами ниже:\n\n"
        "/create_link  — чтобы сгенерировать ссылку на приглашение, которую надо будет отправить другу\n\n"
        "/stats — посмотреть свою статистику по приглашениям",
        reply_markup=keyboard
    )


async def handle_invite_creation(user_id: int, bot: Bot):
    try:
        # Проверяем, есть ли уже ссылка для этого пользователя
        users_data = await get_request(REFERRALS_URL)

        for user_data in users_data:
            if user_data['t_id'] == user_id:
                return f"🔗 Ваша ссылка:\n{user_data['invite_link']}"

        # Если ссылки нет, создаём новую
        invite = await bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            name=f"invite_{user_id}",
            creates_join_request=True
        )

        await post_request(REFERRALS_URL, {
            "t_id": user_id,
            "ref_name": f"invite_{user_id}",
            "invite_link": invite.invite_link,
            "created_at": datetime.datetime.now().isoformat(),
        })

        return f"🔗 Ваша новая ссылка:\n{invite.invite_link}"

    except Exception as e:
        logger.error(f'Error creating invite link for user {user_id}: {e}')
        return "❌ Ошибка во время создании ссылки!\n"


# Обработчик команды /create_invite
@router.message(Command("create_link"))
async def cmd_create_invite(message: Message, bot: Bot):
    response = await handle_invite_creation(message.from_user.id, bot)
    await message.answer(response)


# Обработчик нажатия на кнопку
@router.callback_query(F.data == "create_invite")
async def callback_create_invite(callback_query: CallbackQuery, bot: Bot):
    response = await handle_invite_creation(callback_query.from_user.id, bot)
    await callback_query.message.edit_text(response)
    await callback_query.answer()


async def check_and_notify_first_referral(bot: Bot, referrer_id: str, username: str | None = None):
    try:
        guests_data = await get_request(GUESTS_URL)

        ref_name = f'invite_{referrer_id}'
        ref_guests = [guest for guest in guests_data if guest.get('ref_name') == ref_name]

        if not ref_guests:
            await bot.send_message(referrer_id, GIFT_MESSAGE)
        else:
            message = f"✅ По вашей ссылке к нам пришёл"
            if username:
                message += f"(ла): @{username}"
            else:
                message += " +1 человек"

            await bot.send_message(referrer_id, message)


    except Exception as e:
        logger.error(f"Error in notification task for user {referrer_id}: {e}")


@router.chat_join_request()
async def process_join_request(join_request: ChatJoinRequest, bot: Bot):
    if not join_request.invite_link:
        return

    try:
        guest_data = {
            "t_id": join_request.from_user.id,
            "joined_at": datetime.datetime.now().isoformat(),
            "invite_link": join_request.invite_link.invite_link
        }

        invite_name = join_request.invite_link.name
        if invite_name and invite_name.startswith('invite_'):
            referrer_id = int(invite_name.split('_')[1])

            guest_data.update({
                "ref_id": referrer_id,
                "ref_name": invite_name
            })

            # Уведомляем пригласившего (только в 1й раз)
            asyncio.create_task(
                check_and_notify_first_referral(bot, str(referrer_id), join_request.from_user.username)
            )

        else:
            # Приглашение не было создано через бота
            guest_data.update({
                "ref_id": "",
                "ref_name": invite_name if invite_name else "other invite"
            })

        await post_request(GUESTS_URL, guest_data)
        await join_request.approve()

    except Exception as e:
        logger.error(f"Error saving join request: {e}")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    user_id = message.from_user.id
    try:
        guests_data = await get_request(GUESTS_URL)

        count = 0
        for record in guests_data:
            if record.get('ref_id') == user_id:
                count += 1

        await message.answer(
            f"📊 Ваша статистика:\n\n"
            f"Количество пришедших по вашей ссылке: {count}"
        )

    except Exception as e:
        logger.error(f"Error getting stats for user {user_id}: {e}")
        await message.answer("❌ Ошибка при получении статистики")
