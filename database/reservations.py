import datetime
import sqlite3 as sq


# Установка соединения с БД
def sql_start():
    global base, cur
    base = sq.connect('reservations.db')
    cur = base.cursor()
    if base:
        print('Database is connected')


# Проверка наличия свободных дорожек на указанное время, в определенную дату
async def sql_check_time(date, time, duration):
    end_time = time + int(duration)
    lanes = [1, 2, 3, 4, 5, 6]
    available_lanes = [1, 2, 3, 4, 5, 6]
    for lane in lanes:
        reservations = cur.execute('SELECT lane, time FROM reservation WHERE lane = (?) '
                                   'AND date = (?) AND time BETWEEN (?) AND (?)',
                                   (lane, date, time, end_time - 1)).fetchall()
        if len(reservations) > 0:
            available_lanes.remove(lane)
    if len(available_lanes) > 0:
        return True
    else:
        return False


# Проверка определенной даты на наличие свободных мест (72 - максимальное количество бронирований, при котором
# все дорожки заняты с 12:00 до 24:00)
async def sql_check_date(date):
    reservations = cur.execute('SELECT lane, time FROM reservation WHERE date = (?)', (date,)).fetchall()
    if len(reservations) == 72:
        return False
    else:
        return True


# Добавление новой записи в таблицу предварительных бронирований для дальнейшей обработки менеджером
async def sql_add_reservation(data):
    cur.execute('INSERT INTO not_confirmed_reservation VALUES (?, ?, ?, ?, ?, ?, ?)',
                (None, data['date'], data['time'], data['duration'], data['phone'], data['name'],
                 datetime.datetime.now()))
    base.commit()
