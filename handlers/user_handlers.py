import datetime
from aiogram import types, Dispatcher
from keyboards import mainKeyboard, cancelKeyboard, backKeyboard, send_phone_keyboard, infoKeyboard
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from database import reservations
from bot_creator import bot


# Создаем машину состояний для процедуры бронирования дорожки
class FSMReservation(StatesGroup):
    chooseNumber = State()
    chooseDate = State()
    chooseTime = State()
    sendPhone = State()


async def commands_start(message: types.message):
    await message.answer('Добро пожаловать в Боулинг Клуб Планетарий в городе Жуковский. Я Ваш личный бот-помощник, '
                         'что Вас интересует?', reply_markup=mainKeyboard, disable_notification=True)


async def callbacks_price(callback: types.CallbackQuery):
    await callback.message.answer('<b>Цены:</b>\n\nС понедельника по четверг:\n<b>960 руб.</b>\n\nПятница, суббота, '
                                  'воскресенье, а также праздничные дни:\n<b>1200 руб.</b>\n\nЦены на аренду дорожки '
                                  'в нашем боулинг-клубе указаны за 1 час в рублях с учётом НДС. '
                                  'В стоимость аренды дорожки включено использование специальной обуви '
                                  'для боулинга и шаров.', reply_markup=backKeyboard, disable_notification=True)
    await callback.answer()


async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    # Проверяем, что находимся в каком-либо состоянии из машины состояний, чтобы из него выйти.
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await callback.message.answer('Ок, возвращаемся в главное меню!', reply_markup=types.ReplyKeyboardRemove(),
                                  disable_notification=True)
    await callback.message.answer('Добро пожаловать в Боулинг Клуб Планетарий в городе Жуковский.\n\nЯ Ваш личный '
                                  'бот-помощник, что Вас интересует?',
                                  reply_markup=mainKeyboard, disable_notification=True)
    await callback.answer()


# Отдельный обработчик для кнопки "Назад в меню", т.к. он не предполагает выход из состояний
async def back_handler(callback: types.CallbackQuery):
    await callback.message.answer(
        'Добро пожаловать в Боулинг Клуб Планетарий в городе Жуковский.\n\nЯ Ваш личный бот-помощник, '
        'что Вас интересует?', reply_markup=mainKeyboard, disable_notification=True)
    await callback.answer()


async def callbacks_reservation(callback: types.CallbackQuery):
    await FSMReservation.chooseNumber.set()
    await callback.message.answer('Я помогу Вам забронировать посещение!\n\nЕсли Вам нужно нестандартное бронирование,'
                                  ' например, несколько дорожек на одно и то же время, или Вы хотите отметить '
                                  'день рождения, провести корпоратив, то пожалуйста, позвоните по телефону:  '
                                  '+7(915)200-01-31 \n\nУкажите длительность аренды. Аренда возможна только на целое'
                                  ' количество часов, от 1 до 12. Пришлите целое число.',
                                  reply_markup=cancelKeyboard, disable_notification=True)
    await callback.answer()


async def choose_number(message: types.Message, state: FSMContext):
    try:
        n = int(message.text)
        if 0 < n < 13:
            async with state.proxy() as data:
                data['duration'] = message.text
                await FSMReservation.next()
                await message.answer('Прекрасно, укажите желаемую дату посещения клуба. Дату необходимо '
                                     'прислать в формате DD.MM.YYYY, например 20.08.2023',
                                     reply_markup=cancelKeyboard, disable_notification=True)
        else:
            # Обрабатываем получение значения от пользователя, которое выходит за допустимый диапазон
            await FSMReservation.chooseNumber.set()
            await message.answer('Пожалуйста, введите число от 1 до 12.',
                                 reply_markup=cancelKeyboard, disable_notification=True)
    except ValueError:
        # Обрабатываем неверный формат, например если пользователь пришлет буквенное значение
        await FSMReservation.chooseNumber.set()
        await message.answer('Неверный формат, пожалуйста, введите число. Например "1", без кавычек.',
                             reply_markup=cancelKeyboard, disable_notification=True)


async def choose_date(message: types.Message, state: FSMContext):
    try:
        date = datetime.datetime.strptime(message.text, '%d.%m.%Y')
        if date.date() < datetime.date.today():
            # Обрабатываем возможность указания пользователем для бронирования уже прошедшей даты
            await FSMReservation.chooseDate.set()
            await message.answer('Дата резервирования не может быть в прошлом. Пожалуйста введите корректную дату.',
                                 reply_markup=cancelKeyboard, disable_notification=True)
        else:
            async with state.proxy() as data:
                data['date'] = date.date()
                await FSMReservation.next()
                if await reservations.sql_check_date(data['date']):
                    # Проверяем, что в эту дату вообще есть свободные места
                    await message.answer('Отлично! В какое время Вы хотите посетить клуб? Режим работы клуба с 12:00 '
                                         'до 24:00 ежедневно. В ответ пришлите только число, например для 12:00 '
                                         'пришлите просто 12. Т.к. длительность Вашего сеанса ' + data['duration'] +
                                         ' ч. то максимальное время начала сеанса для Вас: '
                                         + str(24 - int(data['duration'])) + ':00',
                                         reply_markup=cancelKeyboard, disable_notification=True)
                else:
                    await FSMReservation.chooseDate.set()
                    await message.answer('На эту дату свободных бронирований нет. Пожалуйста, введите другую дату.',
                                         reply_markup=cancelKeyboard, disable_notification=True)
    except ValueError:
        # Обрабатываем возможность указания пользователей даты в неверном формате и
        # возможного возникновения ошибок, следующих из этого.
        await FSMReservation.chooseDate.set()
        await message.answer(
            'Неверный формат даты, пожалуйста пришлите дату в формате день.месяц.год, например 20.08.2023',
            reply_markup=cancelKeyboard, disable_notification=True)


async def choose_time(message: types.Message, state: FSMContext):
    try:
        t = int(message.text)
        async with state.proxy() as data:
            if 12 <= t <= (24 - int(data['duration'])):
                data['time'] = message.text
                await FSMReservation.sendPhone.set()
                if await reservations.sql_check_time(data['date'], t, data['duration']):
                    await FSMReservation.sendPhone.set()
                    await message.answer('На эту дату и время есть свободные места! Для подтверждения бронирования '
                                         'Вам позвонит наш менеджер.',
                                         reply_markup=send_phone_keyboard, disable_notification=True)
                    await message.answer('Пожалуйста, пришлите свой номер телефона c помощью кнопки. '
                                         'Если Вы хотите бронировать дорожку на другой номер, пожалуйста'
                                         ' позвоните по тел:  +7(915)200-01-31',
                                         reply_markup=cancelKeyboard, disable_notification=True)
                else:
                    await FSMReservation.sendPhone.set()
                    await message.answer('К сожалению на выбранную дату и время все занято.',
                                         reply_markup=send_phone_keyboard, disable_notification=True)
                    await message.answer('Закажем обратный звонок? Менеджер поможет подобрать свободные дорожки!',
                                         reply_markup=cancelKeyboard, disable_notification=True)

            elif t < 12:
                # Обрабатываем возможное указание пользователем нерабочего времени
                await FSMReservation.chooseTime.set()
                await message.answer('Минимальное время начала сеанса - 12:00. Пожалуйста, пришлите корректное число.',
                                     reply_markup=cancelKeyboard, disable_notification=True)
            else:
                # Обрабатываем возможное указание пользователем нерабочего времени, или времени, в которое не
                # укладывается длительность желаемого сеанса.
                await FSMReservation.chooseTime.set()
                await message.answer('Т.к. длительность Вашего сеанса ' + data['duration'] +
                                     ' ч. то максимальное время начала сеанса для Вас: '
                                     + str(24 - int(data['duration'])) + ':00. Пожалуйста, пришлите корректное число.',
                                     reply_markup=cancelKeyboard, disable_notification=True)
    except ValueError:
        # Обрабатываем неверный формат, например, если пользователь пришлет буквенное значение
        await FSMReservation.chooseTime.set()
        await message.answer(
            'Неверный формат! Пожалуйста, пришлите число, например, 12.',
            reply_markup=cancelKeyboard, disable_notification=True)


async def get_phone(message: types.Message, state: FSMContext):
    contact = message.contact
    async with state.proxy() as data:
        data['phone'] = contact.phone_number
        data['name'] = contact.full_name
        # Записываем в таблицу предварительных бронирований
        await reservations.sql_add_reservation(data)
        await message.answer('Информация передана! Ожидайте звонка от менеджера.',
                             reply_markup=types.ReplyKeyboardRemove(), disable_notification=True)
        await state.finish()
        await message.answer('Спасибо, что выбрали наш боулинг-клуб!',
                             reply_markup=backKeyboard, disable_notification=True)


async def location(callback: types.CallbackQuery):
    await callback.message.answer('Мы находимся в г. Жуковский, по адресу ул. Гагарина, 2А. Вот наш адрес на карте:')
    await bot.send_location(callback.from_user.id, 55.598075, 38.1132,
                            reply_markup=backKeyboard, disable_notification=True)
    await callback.answer()


async def information(callback: types.CallbackQuery):
    await callback.message.answer('Я могу рассказать Вам о внутренних правилах клуба, или о правилах игры в боулинг. '
                                  'Что Вы хотите узнать?', reply_markup=infoKeyboard, disable_notification=True)


async def internal_rules(callback: types.CallbackQuery):
    await callback.message.answer('<b>Общие положения:</b>\n\n1. При наличии очереди оплата за доп. игровое время не'
                                  ' принимается.\n2. После окончания игры в боулинг необходимо вернуть прокатный'
                                  ' инвентарь инструктору клуба.\nГость обязан выполнять требования администратора, '
                                  'инструктора и сотрудников службы контроля.\nВход на площадку для игры в боулинг '
                                  'без сменной обуви категорически запрещен. За несоблюдение требования взимается '
                                  'штраф.\nПосещая Клуб, не оставляйте личные вещи и одежду без присмотра. За утерянные'
                                  ' оставленные без присмотра или забытые вещи, ценности администрация Клуба '
                                  'ответственности не несет.', disable_notification=True)
    await callback.message.answer('<b> Запрещается:</b>\n\n1. Отвлекать персонал и мешать его работе.\n2.Мешать отдыху'
                                  ' других посетителей.\n3.Входить в игровую зону без спец. обуви, а также покидать '
                                  'помещение клуба в спец. обуви (выходить на улицу).', disable_notification=True)
    await callback.message.answer('<b>В игровой зоне запрещается:</b>\n\n1. Бросать шар при опущенном уборщике кегель,'
                                  ' возможна поломка машины из-за попадания шара в уборщик.\n2. Бросать шар на '
                                  'неосвещенную дорожку.\n3. Курить в зоне отдыха и находиться в зоне разбега с '
                                  'напитками и продуктами питания.\n4. Заходить за линию фола в зоне разбега.\n5.'
                                  'Кидать два шара одновременно на одну дорожку.\n6.Находиться более одного человека в '
                                  'зоне разбега одной дорожки.\n7.Производить добивание оставшихся кегель после 3-го '
                                  'броска в 10-ом фрейме.', disable_notification=True)
    await callback.message.answer('<b>При несоблюдении этих требований, если это вызвало порчу оборудования, клиент '
                                  'выплачивает сумму причиненного ущерба в полном размере.</b>',
                                  reply_markup=backKeyboard, disable_notification=True)
    await callback.answer()


async def bowling_rules(callback: types.CallbackQuery):
    await callback.message.answer('<b>Коротко о боулинге:</b>\n\nСамый популярный вариант игры в боулинг — это игра по '
                                  'системе «десяти кеглей». Она состоит из десяти «ходов» каждого игрока — <b>фреймов. '
                                  '</b>В каждом фрейме игрок может совершить два броска шара, за исключением последнего'
                                  ' фрейма (в некоторых случаях).', disable_notification=True)
    await callback.message.answer('Если в начале фрейма игрок сразу сбивает одним ударом все 10 кеглей, то фрейм удачно'
                                  ' завершается, это называется — <b>страйк</b>.\nЕсли хотя бы одна из кегель устояла, '
                                  'шар бросается во второй раз. Кегли, сбитые за две попытки, называются <b>спэр</b> '
                                  'Если игроку не удается сбить все кегли за два броска шара в одном фрейме, то фрейм '
                                  'остается открытым, если только кегли продолжающие стоять после первого броска шара '
                                  'не образуют <b>сплит</b>. Сплитом называется такое положение нескольких кеглей, '
                                  'оставшихся стоять после первого броска шара, при котором первая (головная) кегля '
                                  'упала, а две кегли или более остались, но не рядом стоящие.',
                                  disable_notification=True)
    await callback.message.answer('Два и три последовательных страйка называются соответственно <b>даблом (double) и '
                                  'триплом (triple)</b>. В десятом фрейме игрок бросает три шара, если он сделал страйк'
                                  ' или выбил спэр.', disable_notification=True)
    await callback.message.answer('<b>Подсчет очков:</b>\n\nОчки, набранные в каждом фрейме, рассчитываются как сумма '
                                  'сбитых в данном фрейме кеглей и призовых очков. За открытые фреймы, где не были '
                                  'сбиты все кегли, начисляется количество очков, равное лишь количеству сбитых кеглей.'
                                  ' Призовые очки игрок получает, только если он сделал страйк или выбыл спэр. Один '
                                  'страйк оценивается в 10 очков плюс призовые очки, равные числу кеглей, сбитых '
                                  'игроком за последующие два броска шара. За спэр начисляется 10 очков плюс число '
                                  'кеглей, сбитых игроком при последующем броске шара.', disable_notification=True)
    await callback.message.answer('<b>Идеальная игра:</b>\n\nМаксимальное количество очков, которые можно набрать в '
                                  'одном фрейме, равно тридцати (в том случае, если за страйком следуют еще два '
                                  'страйка), а целиком за игру — триста очков, то есть двенадцать страйков подряд. '
                                  'Фактически, игры с высокими результатами (свыше 200 очков) возможны лишь при '
                                  'нескольких подряд сделанных страйках, что является показателем высокого мастерства '
                                  'игрока. Игры с количеством максимальным количеством очков (300) называются '
                                  '<b>perfect game</b> («идеальная игра» по-английски).',
                                  reply_markup=backKeyboard, disable_notification=True)
    await callback.answer()


async def promo(callback: types.CallbackQuery):
    await callback.message.answer('<b>Акции действующие на данный момент:</b>\n\n <b>Скидка в день рождения!</b>\n'
                                  'Приходите праздновать день рождения в наш клуб и получите 10% скидку! '
                                  'Для получения скидки, при подтверждении бронирования, укажите на это менеджеру. '
                                  'При посещении, не забудьте документ, подтверждающий право на скидку, иначе она '
                                  'будет аннулирована.', disable_notification=True)
    await callback.message.answer('<b>Страйк-Меню!</b>\n\nИграйте в боулинг, выбивайте страйки - получайте подарки!\n\n'
                                  '<b>3 страйка:</b>\n- жетон для игровых автоматов (2шт.)\n- Кока-кола (0.33л)\n'
                                  '- пиво (0.33л)\n\n<b>4 страйка:</b>\n- жетон для игровых автоматов (4шт.)\n- '
                                  'Кока-кола (0.5л)\n- пиво (0.5л)\n\n<b>Условия:</b>\n1. Страйки должны быть выбиты '
                                  'подряд, в одной игре из 10 фреймов, одним игроком.\n2. Алкогольная продукция, '
                                  'выдаваемая в качестве приза, не может быть выдана лицам, не достигшим 18-ти летнего'
                                  ' возраста.\n3. В случае игры по бесплатным сертификатам призы за выбитые '
                                  'страйки не выдаются.', reply_markup=backKeyboard, disable_notification=True)
    await callback.answer()


# Регистрируем обработчики для вызова из main.py
def register_handlers_user(dp: Dispatcher):
    dp.register_message_handler(commands_start, commands=['start'])
    dp.register_callback_query_handler(callbacks_price, text='Цены')
    dp.register_callback_query_handler(callbacks_reservation, text='Бронирование')
    dp.register_callback_query_handler(back_handler, text='Назад')
    dp.register_callback_query_handler(location, text='Карта')
    dp.register_callback_query_handler(information, text='Информация')
    dp.register_callback_query_handler(internal_rules, text='Внутренние')
    dp.register_callback_query_handler(bowling_rules, text='Боулинг')
    dp.register_callback_query_handler(promo, text='Акции')

    dp.register_message_handler(get_phone, content_types=types.ContentType.CONTACT, state=FSMReservation.sendPhone)
    dp.register_message_handler(choose_number, state=FSMReservation.chooseNumber)
    dp.register_message_handler(choose_date, state=FSMReservation.chooseDate)
    dp.register_message_handler(choose_time, state=FSMReservation.chooseTime)

    dp.register_callback_query_handler(cancel_handler, state="*", text='Отмена')

