Сервер запускал через PyCharm, run

Конфигурация необходимая в серверной составляющей:

CONVERSATION_API_URL – url внешнего API

CONVERSATION_API_KEY – ключ внешнего API

Порт сервера

Директория хранения кэша

По умолчанию сервер запустится на [http://0.0.0.0:8000](http://0.0.0.0:8000)

POST /conversation

Основной endpoint для обработки команд и генерации аудио ответа.

Запрос

curl -X POST [http://192.168.137.1:8000/conversation](http://192.168.137.1:8000/conversation) \

-H "Content-Type: application/json" \

-d '{

```
"user_text": "запрос",

"speaker": "baya",

"sample_rate": 48000
```

}'

Ответ

{

```
"audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",

"sample_rate": 48000,

"user_text": "запрос",

"bot_response": "Ответ со строны API",

"is_error": false,

"message": "Success"
```

}

Если внешнего API нет, или оно не работает робот возвращает данную ему фразу

Все файлы робота должны находиться в одной дирректории, робот запускается через терминал -> cd .. в необходимую директорию и командой python3 image.py без sudo

Конфигурацию робота можно сделать в config.py

Проверка аудио можно совершить через python3 setup_audio.py и alsamixer для установки уровня громкости

Управление робота работает через R – переход в ручной или автоматический режим, wasd – управление spacebar – остановка на месте, Q – выключение скрипта, P – пауза.

Для настройки самих глаз используется config.py

Чтобы изменить вызов глаз в определенный момент поведения нужно изменить вызов глаз в коде

Зависимости необходимые серверу:

| Библиотека             | Версия    |
| ---------------------- | --------- |
| Flask                  | 3.1.2     |
| Flask-SocketIO         | 5.6.0     |
| Jinja2                 | 3.1.6     |
| MarkupSafe             | 3.0.3     |
| PyYAML                 | 6.0.3     |
| Werkzeug               | 3.1.5     |
| annotated-types        | 0.7.0     |
| antlr4-python3-runtime | 4.9.3     |
| anyio                  | 4.12.1    |
| bidict                 | 0.23.1    |
| blinker                | 1.9.0     |
| certifi                | 2026.2.25 |
| cffi                   | 2.0.0     |
| charset-normalizer     | 3.4.4     |
| click                  | 8.3.1     |
| colorama               | 0.4.6     |
| fastapi                | 0.117.0   |
| filelock               | 3.20.3    |
| fsspec                 | 2026.1.0  |
| h11                    | 0.16.0    |
| idna                   | 3.11      |
| itsdangerous           | 2.2.0     |
| mpmath                 | 1.3.0     |
| networkx               | 3.6.1     |
| numpy                  | 2.4.2     |
| omegaconf              | 2.3.0     |
| pip                    | 23.2.1    |
| pycparser              | 3.0       |
| pydantic               | 2.12.5    |
| pydantic_core          | 2.41.5    |
| python-engineio        | 4.13.0    |
| python-multipart       | 0.0.20    |
| python-socketio        | 5.16.0    |
| requests               | 2.31.0    |
| setuptools             | 80.10.2   |
| simple-websocket       | 1.1.0     |
| soundfile              | 0.13.1    |
| starlette              | 0.48.0    |
| sympy                  | 1.14.0    |
| torch                  | 2.10.0    |
| torchaudio             | 2.10.0    |
| typing-inspection      | 0.4.2     |
| typing_extensions      | 4.15.0    |
| urllib3                | 2.6.3     |
| uvicorn                | 0.37.0    |
| wsproto                | 1.3.2     |

Комманда для установки зависимостей:
pip install Flask==3.1.2 Flask-SocketIO==5.6.0 Jinja2==3.1.6 MarkupSafe==3.0.3 PyYAML==6.0.3 Werkzeug==3.1.5 annotated-types==0.7.0 antlr4-python3-runtime==4.9.3 anyio==4.12.1 bidict==0.23.1 blinker==1.9.0 certifi==2026.2.25 cffi==2.0.0 charset-normalizer==3.4.4 click==8.3.1 colorama==0.4.6 fastapi==0.117.0 filelock==3.20.3 fsspec==2026.1.0 h11==0.16.0 idna==3.11 itsdangerous==2.2.0 mpmath==1.3.0 networkx==3.6.1 numpy==2.4.2 omegaconf==2.3.0 pip==23.2.1 pycparser==3.0 pydantic==2.12.5 pydantic_core==2.41.5 python-engineio==4.13.0 python-multipart==0.0.20 python-socketio==5.16.0 requests==2.31.0 setuptools==80.10.2 simple-websocket==1.1.0 soundfile==0.13.1 starlette==0.48.0 sympy==1.14.0 torch==2.10.0 torchaudio==2.10.0 typing-inspection==0.4.2 typing_extensions==4.15.0 urllib3==2.6.3 uvicorn==0.37.0 wsproto==1.3.2

Зависимости необходимые для работы робота:

sudo apt-get update

sudo apt-get install -y python3-pip python3-venv portaudio19-dev python3-pyaudio \

python3-pygame python3-rpi.gpio python3-xlib libatlas-base-dev libjasper-dev libqt5gui5

sudo apt-get install -y flac ffmpeg

| Библиотека        | Версия |
| ----------------- | ------ |
| pygame            | 2.0.0  |
| SpeechRecognition | 3.8.0  |
| requests          | 2.25.0 |
| psutil            | 5.8.0  |
| PyAudio           | 0.2.11 |
| numpy             | 1.19.0 |
| python-xlib       | 0.29   |
| RPi.GPIO          | 0.7.0  |

Комманда для установки зависимостей:
pip3 install pygame==2.0.0 SpeechRecognition==3.8.0 requests==2.25.0 psutil==5.8.0 numpy==1.19.0 python-xlib==0.29
