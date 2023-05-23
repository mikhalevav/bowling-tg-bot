from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Создаем кнопки для главного меню
price_button = InlineKeyboardButton(text='\U0001F4B8 Цены', callback_data='Цены')
reservation_button = InlineKeyboardButton(text='\u270F Бронирование', callback_data='Бронирование')
info_button = InlineKeyboardButton(text='\u2139 Информация', callback_data='Информация')
promo_button = InlineKeyboardButton(text='\U0001F31F Акции', callback_data='Акции')
location_button = InlineKeyboardButton(text='\U0001F4CD Показать на карте', callback_data='Карта')

# Создаем ситуативные кнопки - отправка номера, отмена, назад.
send_phone_button = KeyboardButton('Отправить номер телефона', request_contact=True)
cancel_button = InlineKeyboardButton(text='Отмена', callback_data='Отмена')
back_button = InlineKeyboardButton(text='Назад в меню', callback_data='Назад')

# Создаем кнопки для меню с информацией
internal_rules_button = InlineKeyboardButton(text='Внутренние правила', callback_data='Внутренние')
bowling_rules_button = InlineKeyboardButton(text='Правила игры', callback_data='Боулинг')

# Создаем необходимые нам клавиатуры из ранее созданных кнопок
mainKeyboard = InlineKeyboardMarkup(row_width=2).add(price_button, reservation_button)\
                                                .add(promo_button, info_button).add(location_button)
infoKeyboard = InlineKeyboardMarkup(row_width=2).add(internal_rules_button, bowling_rules_button).add(back_button)
cancelKeyboard = InlineKeyboardMarkup(row_width=1).add(cancel_button)
backKeyboard = InlineKeyboardMarkup(row_width=1).add(back_button)
send_phone_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(send_phone_button)


