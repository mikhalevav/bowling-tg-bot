from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import config

# Объявляем место хранения данных до их записи в БД
storage = MemoryStorage()

# Получаем токен из config файла, устанавливаем тип HTML для форматирования текста.
bot = Bot(token=config.TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=storage)