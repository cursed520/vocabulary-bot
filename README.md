# Language Learning Bot 🤖

Discord-бот для изучения английских слов через викторину.

## Команды
- `!word_ru <русское> <английское>` — добавить слово
- `!quiz` — начать викторину
- `!stats` — моя статистика
- `!top` — таблица лидеров

## Установка
1. `pip install -r requirements.txt`
2. Создать `config.py` с токеном бота
3. Запустить: `python main.py`

## Технологии
- Python 3.12
- discord.py
- SQLAlchemy (async)
- SQLite