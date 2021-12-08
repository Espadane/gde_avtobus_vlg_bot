from os import getenv
from sys import exit
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
import emoji
from parser import *

bot_token = getenv("BOT_TOKEN")
if not bot_token:
    exit("Error: no token provided")

bot = Bot(token=bot_token)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def process_start_command(msg: types.Message):
    """Обработчик команды '/start'"""
    await msg.reply(f"Привет, {msg.from_user.first_name}!\nЯ могу помочь тебе узнать когда ты уедешь домой, просто пришли мне номер маршрута который тебя интересует.\nПо всем вопросам и предложениям пиши @Espadane")
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text="Отправить местоположение", request_location=True))
    keyboard.add(types.KeyboardButton(text="Памагите!"))
    await msg.answer("Выберите действие:", reply_markup=keyboard)

@dp.message_handler(commands=['count'])
async def count_users(msg: types.Message):
    '''Сообщение с выводом списка пользователей и их количеством'''
    user_id = msg.from_user.id
    if user_id == 178080841:
        users = append_user(user_id)
        await msg.answer('Общее количество пользователей:\n' + str(len(users)))
        await msg.answer(users)



@dp.message_handler(commands=['help'])
@dp.message_handler(Text(equals="Памагите!"))
async def process_start_command(msg: types.Message):
    """Обработчик команды '/help'"""
    await msg.answer(f'Пришлите мне номер маршрута, чтобы узнать где транспорт. Затем выбери в какую тебе сторону. Я покажу тебе в какой момент ты уедешь.\nЧтобы узнать ближайшие остановки, что и когда там ходит, нажми кнопку "Отправить местоположение". В ответ я тебе пришлю остановки на расстоянии 750м. По клику на остановку, я покажу расписание.')

@dp.message_handler(Text)
async def answer(msg:types.Message):
    """Обработка вывода расписания по номеру маршрута"""
    user_id = msg.from_user.id
    user_name = msg.from_user.first_name
    append_user(user_id)
    response = msg.text.upper()
    result = read_route_from_json(response)
    if result == None:
        await msg.reply(f'Простите хозяин, я не знаю такого маршрута. Ну или сайт, не дает данных.')
    else:
        number = result.get('number')
        transport = result.get('transport')
        destination = result.get('destination')
        url = result.get('url')
        await msg.answer(f'Вы выбрали маршрут номер - {number}, это {transport}\nСледует по маршруту {destination}')
        directions = get_direction(url)
        if directions == '404':
            await msg.answer("Сайт временно не доступен, приносим извинения за неудобства.")
        else:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text=f'{directions[0]}', callback_data="up"))
            keyboard.add(types.InlineKeyboardButton(text=f'{directions[1]}', callback_data="down"))
            await msg.answer(f"<a href = '{url}'>Посмотреть маршрут полностью</a>", reply_markup=keyboard,parse_mode=types.ParseMode.HTML )

@dp.callback_query_handler(text='up')
@dp.callback_query_handler(text='down')
async def get_schedule(call: types.CallbackQuery):
        url = str(call.message.entities[0]['url'])
        """Обработка выбора направления следования маршрута"""
        if call.data == 'up':
            url = url + '&rl_racetype=65'
        elif call.data == 'down':
            url = url + '&rl_racetype=66'
        shedulle = get_shedulle_from_url(url)
        r = ''
        for s in shedulle:
            arrow = arrow = emoji.emojize(':right_arrow:')
            stop_time = s['stop_time']
            stop_title = s['stop_title']
            r = r + f'\n=========\n{stop_title} {arrow}  <b>{stop_time}</b>'
        await call.message.answer(r, parse_mode=types.ParseMode.HTML)

@dp.message_handler(content_types=['location'])
async def handle_location(msg: types.Message):
    """Получение данных местоположения и вывод кнопок"""
    latittude = msg.location.latitude
    longitude = msg.location.longitude
    try:
        stops = get_stops_nearby_data(latittude, longitude)
        for stop in stops:
            stop_url = stop['stop_url']
            stop_title = stop['stop_title']
            button=(types.InlineKeyboardButton(text=f"{stop_title} ", callback_data='show_routes'))
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(button)
            await msg.answer(f"<a href = '{stop_url}'>Посмотреть полное расписание</a>", reply_markup=keyboard,disable_web_page_preview=True, parse_mode=types.ParseMode.HTML)
    except:
        await msg.answer(f"Рядом в ближайшее время не будет транспорта. Либо уже поздно и он весь лег спать, либо сайт не доступен.",disable_web_page_preview=True, parse_mode=types.ParseMode.HTML)

@dp.callback_query_handler(text='show_routes')
async def show_routes(call: types.callback_query):
    """Вывод ближайшего транспорта на остановке"""
    url = str(call.message.entities[0]['url'])
    routes = get_routes_nearby_data(url)
    answer = ''
    for route in routes:
        route_number = route['route_number']
        route_transport = ''
        if 'Тб.' in str(route_number):
            route_transport = emoji.emojize("\n==================\n:trolleybus:")
            route_number = str(route_number).replace('Тб.','').replace('.','')
        elif 'Тр.' in str(route_number):
            route_transport = emoji.emojize("\n==================\nn:train2:")
            route_number = str(route_number).replace('Тр.','').replace('.','')
        else:
            route_transport = emoji.emojize("\n==================\n:bus:")
            route_number = str(route_number).replace('.','')
        spaces = 4 - len(route_number)
        spaces = '  '* spaces
        route_time = route['route_time']
        arrow = emoji.emojize(':right_arrow:')
        res = f'{route_transport}   {route_number}{spaces}   {arrow}   <b>{route_time}</b>'
        answer = answer + res

    await call.message.answer(answer, parse_mode=types.ParseMode.HTML)


if __name__ == '__main__':
    executor.start_polling(dp)