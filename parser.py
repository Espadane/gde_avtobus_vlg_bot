import os, time
import requests
from bs4 import BeautifulSoup
import json


url = 'https://transport.volganet.ru/wap/online/'

def append_user(user_id):
    '''Добавление пользователя в список пользователей'''
    with open ('users') as file:
        users = ''.join(file.readlines()).strip().split('\n')
        if str(user_id) not in users:
            with open('users','a') as file:
                file.write(str(user_id))
        
        return users


def get_html(url):
    """Получаем html с основного сайта"""
    header = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'}
    r = requests.get(url=url, headers=header)
    if r.status_code != 200:
        return 200
    else:
        print(f'Status code: {r.status_code}')
        soup = BeautifulSoup(r.text, 'lxml')
        
        return soup 

def get_routes_json():
    """Получаем список маршрутов и пишем их в json"""
    html = get_html(url)
    routes = html.find_all('a')
    routes_list = []
    for route in routes:
        route_url = str(route.get('href'))
        if 'mr_id' not in route_url or route_url == None:
            route_url = '-'
        else:
            route_url = 'https://transport.volganet.ru/wap/online/'+ route_url 
        route_number = route.find('span')
        if route_number == None or route_number == 'тест':
            route_number = '-'
        else:
            route_number = route_number.text
        route_destination = str(route.find('p')).replace('<p>', '').replace('</p>', '')
        if route_destination == 'None' or route_destination == 'тест':
            route_destination = '-'
        route_color = str(route.find('div'))
        if 'bg-blue' in route_color:
            route_transport = 'Трамвай'
        elif 'bg-green' in route_color:
            route_transport = 'Автобус'
        elif 'bg-red' in route_color:
            route_transport = 'Тролейбус'
        else:
            route_transport = '-'

        if '-' == route_destination:
            continue
        else:
            routes_list.append({route_number:{
                'number' : route_number,
                'url' : route_url,
                'destination' : route_destination,
                'transport' : route_transport,
                }})

    with open ('routes.json', 'w', encoding='utf8') as file:
        json.dump(routes_list, file, indent=4, ensure_ascii=False)

def check_routes_json():
    """Проверяем есть ли список маршрутов и обновляем его каждый день"""
    check_file = os.path.exists('routes.json')
    if check_file == True:
        last_modified = os.path.getatime('routes.json')
        now = time.time()
        time_difference = now - last_modified
        if int(time_difference) > 86400:
            get_routes_json()
            print('Файл с маршрутами создан')

    else:
        get_routes_json()
        print('Файл с маршрутами обновлен')

def read_route_from_json(number):
    """Чтение списка маршрутов"""
    check_routes_json()
    with open('routes.json', encoding='utf8') as f:
        routes = json.load(f)
    for route in routes:
        if route.get(number):

            return route.get(number)

def get_direction(url):
    """Получаем направления движения транспорта"""
    try:
        html = get_html(url)
    except Exception as e:
        print(e)
        return '404'
    direction = []
    directions = html.find_all('td')
    for i in directions:
        try:
            result = i.text
            if len(result) > 5:
                direction.append(result)
        except:
            continue
    
    return direction

def get_shedulle_from_url(url):
    """Получаем расписание, название остановки и время прибытия"""
    shedulle = []
    html = get_html(url)
    stops = html.find_all('tr')
    for stop in stops:
        stop_title = stop.find('a').text
        stop_time = stop.find('td').text
        if 'до ост.' not in stop_title:
            shedulle.append({'stop_title': stop_title,
                            'stop_time':stop_time})

    return shedulle

def get_stops_nearby_data(latittude, longitude):
    '''Получаем данные об остановках рядом с местоположением пользователя'''
    url = f'https://transport.volganet.ru/wap/find/?op=coor&lat={latittude}&long={longitude}'
    # url = f'https://transport.volganet.ru/wap/find/?op=coor&lat=48.709542&long=44.520638' #тестовый урл 
    html = get_html(url)
    try:
        stops = html.find_all('tr', align="center")
    except Exception as e:
        print(e)
        return '404'
    stops_data = []
    for stop in stops:
        stops_nearby = stop.find_all('a')
        for stop_nearby in stops_nearby:
            stop_title = stop_nearby.text
            stop_url = stop_nearby.get('href')
            stop_url = 'https://transport.volganet.ru/wap' + str(stop_url)[2:]
            stops_data.append({
                            'stop_title': stop_title,
                            'stop_url': stop_url
            })

    return stops_data

def get_routes_nearby_data(url):
    """Получаем маршруты на остановках рядом"""
    html = get_html(url)
    try:
        routes = html.find('tbody').find_all('tr')
        routes_nearby = []
    except Exception as e:
        print(e)


    for i in routes:
        route = i.find_all('td')
        try:
            route_number = route[0].find('a').text
            if ':' in str(route_number):
                continue
        except:
            continue

        try:
            route_time = route[2].find('a').text
        except:
            continue

        routes_nearby.append({'route_number' : route_number,
                                'route_time' : route_time})

    return routes_nearby[:6]