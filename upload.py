from flask import Flask, request, jsonify
import logging

import json
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}
animal = 'слон'


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(request.json, response)

    logging.info('Response: %r', request.json)

    return jsonify(response)


def handle_dialog(req, res):
    global animal
    user_id = req['session']['user_id']

    if req['session']['new']:

        sessionStorage[user_id] = {
            'suggests': [
                "Не хочу.",
                "Не буду.",
                "Отстань!",
            ]
        }
        # Заполняем текст ответа
        res['response']['text'] = f'Привет! Купи {animal}а!'
        # Получим подсказки
        res['response']['buttons'] = get_suggests(user_id)
        return

    if any(x in req['request']['original_utterance'].lower() for x in ['ладно', 'куплю', 'покупаю', 'хорошо']):
        # Пользователь согласился, прощаемся.
        res['response']['text'] = f'{animal} можно найти на Яндекс.Маркете!'
        if animal == 'кролик':
            res['response']['end_session'] = True
        else:
            animal = 'кролик'
        res['response']['text'] += '\nА теперь купи кролика'
        sessionStorage[user_id] = {
            'suggests': [
                "Не хочу.",
                "Не буду.",
                "Отстань!",
            ]
        }
        res['response']['buttons'] = get_suggests(user_id)
        return

    # Если нет, то убеждаем его купить слона!
    res['response']['text'] = f'Все говорят "%s", а ты купи {animal}!' % (
        req['request']['original_utterance']
    )
    res['response']['buttons'] = get_suggests(user_id)


def get_suggests(user_id):
    session = sessionStorage[user_id]

    # Выбираем две первые подсказки из массива.
    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests'][:2]
    ]

    # Убираем первую подсказку, чтобы подсказки менялись каждый раз.
    session['suggests'] = session['suggests'][1:]
    sessionStorage[user_id] = session

    # Если осталась только одна подсказка, предлагаем подсказку
    # со ссылкой на Яндекс.Маркет.
    if len(suggests) < 2:
        suggests.append({
            "title": "Ладно",
            "url": f"https://market.yandex.ru/search?text={animal}",
            "hide": True
        })

    return suggests


if __name__ == '__main__':
    app.run()
