from flask import Flask, request, jsonify
import logging
from mtranslate import translate

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)


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
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return jsonify(response)


def handle_dialog(res, req):
    if req['session']['new']:
        res['response'][
            'text'] = 'Привет! Для перевода слов запиши их в формате - «Переведите (переведи) слово *слово*»'
        return

    text = req['request']['command']
    if 'переведите слово ' == text[:17]:
        res['response']['text'] = translate(text[16:], "eng", "rus")
    elif 'переведи слово ' == text[:15]:

        res['response']['text'] = translate(text[16:], "eng", "rus")
    else:
        res['response']['text'] = 'Ивините я не понимаю ваш запрос, повторите его пожалуйста'


if __name__ == '__main__':
    app.run()
