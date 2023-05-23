import os

from aiogram.utils import executor

import config
from bot_creator import dp, bot
from database import reservations


async def on_startup(dp):
    await bot.set_webhook(config.URL_APP)
    reservations.sql_start()


async def on_shutdown(dp):
    await bot.delete_webhook()


from handlers import user_handlers

# Обработчики пользователя
user_handlers.register_handlers_user(dp)


executor.start_webhook(
    dispatcher=dp,
    webhook_path='',
    on_startup=on_startup,
    on_shutdown=on_shutdown,
    skip_updates=True,
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 80))
)
