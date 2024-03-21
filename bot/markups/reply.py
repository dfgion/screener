from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

skip_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Пропустить')
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
timeframes_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='1')
        ],
        [
            KeyboardButton(text='2')
        ],
        [
            KeyboardButton(text='3')
        ],
        [
            KeyboardButton(text='4')
        ],
        [
            KeyboardButton(text='5')
        ],
        [
            KeyboardButton(text='10')
        ],
        [
            KeyboardButton(text='20')
        ],
        [
            KeyboardButton(text='30')
        ],
        [
            KeyboardButton(text='60')
        ],
    ]
)