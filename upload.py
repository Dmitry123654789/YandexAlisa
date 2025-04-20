from flask import Flask, request, jsonify
import logging
import random
import requests

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': ['Россия', ['213044/cf0852c67acc571950d7', '1652229/bfc3768d9f320fb7577f']],
    'нью-йорк': ['США', ['1652229/5cca3268f24457221536', '937455/53f4bbc22ef006a181aa']],
    'париж': ['Франция', ["1656841/87a1a3139860451c92a6", '937455/8ddabc5a8e53b6deac11']]
}

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False,
            "buttons": [
                {
                    "hide": True,
                    "title": "Помощь"
                }
            ]
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return jsonify(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False
        }
        return

    if 'помощь' in req['request']['nlu']['tokens']:
        res['response'][
            'text'] = 'Это простая игра, где тебе нужно угадывать города.\nВ момент игры у тебя будет две попытки угадать город, но не бойся тебе хватит и одной попытки ведь игра совсем не сложная'
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            # создаём пустой массив, в который будем записывать города, которые пользователь уже отгадал
            sessionStorage[user_id]['guessed_cities'] = []
            # как видно из предыдущего навыка, сюда мы попали, потому что пользователь написал своем имя.
            # Предлагаем ему сыграть и два варианта ответа "Да" и "Нет".
            res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. Я Алиса. Отгадаешь город по фото?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]
    else:
        if not sessionStorage[user_id]['game_started']:
            if 'да' in req['request']['nlu']['tokens']:
                if len(sessionStorage[user_id]['guessed_cities']) == 3:
                    res['response']['text'] = 'Ты отгадал все города!'
                    res['response']['end_session'] = True
                else:
                    sessionStorage[user_id]['game_started'] = True
                    sessionStorage[user_id]['attempt'] = 1
                    # функция, которая выбирает город для игры и показывает фото
                    play_game(res, req)
            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                res['response']['end_session'] = True
            else:
                res['response']['text'] = 'Не поняла ответа! Так да или нет?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },
                    {
                        "hide": True,
                        "title": "Помощь"
                    }
                ]
        else:
            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    if attempt == 1:
        # если попытка первая, то случайным образом выбираем город для гадания
        city = random.choice(list(cities))
        # выбираем его до тех пор пока не выбираем город, которого нет в sessionStorage[user_id]['guessed_cities']
        while city in sessionStorage[user_id]['guessed_cities']:
            city = random.choice(list(cities))
        # записываем город в информацию о пользователе
        sessionStorage[user_id]['city'] = city
        sessionStorage[user_id]['is_city'] = True
        # добавляем в ответ картинку
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за город?'
        res['response']['card']['image_id'] = cities[city][1][attempt - 1]
        res['response']['text'] = 'Тогда сыграем!'
    else:
        city = sessionStorage[user_id]['city']
        if not sessionStorage[user_id]['is_city']:
            try:
                country = req['request']['nlu']['entities']['value']['country']
            except KeyError:
                country = None
            if country == cities[city][0]:
                res['response']['text'] = 'Правильно! Сыграем ещё?'
                sessionStorage[user_id]['guessed_cities'].append(city)
                sessionStorage[user_id]['game_started'] = False
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },
                    {
                        "hide": True,
                        "title": "Помощь"
                    },
                    {
                        "hide": True,
                        "title": "Покажи город на карте",
                        "url": f'https://yandex.ru/maps/?mode=search&text={city}'
                    }
                ]
                return
            else:
                res['response']['text'] = f'Вы пытались. Это {cities[city][0][0]}. Сыграем ещё?'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_cities'].append(city)
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },
                    {
                        "hide": True,
                        "title": "Помощь"
                    },
                    {
                        "hide": True,
                        "title": "Покажи город на карте",
                        "url": f'https://yandex.ru/maps/?mode=search&text={city.title()}'
                    }
                ]
                return

        if get_city(req) == city:
            # если отгодали
            res['response']['text'] = 'Правильно! А в какой стране этот город?'
            sessionStorage[user_id]['is_city'] = False
            # sessionStorage[user_id]['guessed_cities'].append(city)
            # sessionStorage[user_id]['game_started'] = False
            res['response']['buttons'] = [
                {
                    "hide": True,
                    "title": "Помощь"
                },
                {
                    "hide": True,
                    "title": "Покажи город на карте",
                    "url": f'https://yandex.ru/maps/?mode=search&text={city}'
                }
            ]
            return
        else:
            # если нет
            if attempt == 3:
                # если попытка третья, то значит, что все картинки мы показали.
                # В этом случае говорим ответ пользователю,
                # добавляем город к sessionStorage[user_id]['guessed_cities'] и отправляем его на второй круг.
                # Обратите внимание на этот шаг на схеме.
                res['response']['text'] = f'Вы пытались. Это {city.title()}. Сыграем ещё?'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_cities'].append(city)
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },
                    {
                        "hide": True,
                        "title": "Помощь"
                    },
                    {
                        "hide": True,
                        "title": "Покажи город на карте",
                        "url": f'https://yandex.ru/maps/?mode=search&text={city.title()}'
                    }
                ]
                return
            else:
                # иначе показываем следующую картинку
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Неправильно. Вот тебе дополнительное фото'
                res['response']['card']['image_id'] = cities[city][1][attempt - 1]
                res['response']['text'] = 'А вот и не угадал!'
    # увеличиваем номер попытки доля следующего шага
    sessionStorage[user_id]['attempt'] += 1


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


def get_geo_info(city_name, type_info):
    if type_info == 'coordinates':
        try:
            # url, по которому доступно API Яндекс.Карт
            url = "https://geocode-maps.yandex.ru/1.x/"
            # параметры запроса
            params = {
                "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
                # город, координаты которого мы ищем
                'geocode': city_name,
                # формат ответа от сервера, в данном случае JSON
                'format': 'json'
            }
            # отправляем запрос
            response = requests.get(url, params)
            # получаем JSON ответа
            json = response.json()
            # получаем координаты города
            # (там написаны долгота(longitude), широта(latitude) через пробел)
            # посмотреть подробное описание JSON-ответа можно
            # в документации по адресу https://tech.yandex.ru/maps/geocoder/
            coordinates_str = json['response']['GeoObjectCollection'][
                'featureMember'][0]['GeoObject']['Point']['pos']
            # Превращаем string в список, так как
            # точка - это пара двух чисел - координат
            long, lat = map(float, coordinates_str.split())
            # Вернем ответ
            return long, lat
        except Exception as e:
            return e

    elif type_info == 'country':
        try:
            url = "https://geocode-maps.yandex.ru/1.x/"
            params = {
                "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
                'geocode': city_name,
                'format': 'json'
            }
            data = requests.get(url, params).json()
            # все отличие тут, мы получаем имя страны
            return data['response']['GeoObjectCollection'][
                'featureMember'][0]['GeoObject']['metaDataProperty'][
                'GeocoderMetaData']['AddressDetails']['Country']['CountryName']
        except Exception as e:
            return e


if __name__ == '__main__':
    app.run()
