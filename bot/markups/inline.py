from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='Изменить рост', callback_data='change_long')
    ],
    [
        InlineKeyboardButton(text='Изменить просадку', callback_data='change_short')
    ],
    [
        InlineKeyboardButton(text='Начать сканирование', callback_data='start_scan')
    ],
    [
        InlineKeyboardButton(text='Остановить сканирование', callback_data='stop_scan')
    ],
    [
        InlineKeyboardButton(text='Текущие настройки', callback_data='options')
    ],
])