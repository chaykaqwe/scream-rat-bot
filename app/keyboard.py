from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

start = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Получить крысу🐀')]], resize_keyboard=True)
stop_scream = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='НАКОРМИТЬ БРАУНИ🍮')]])
main = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Погладить крысу', callback_data='squish_rat')],
                                             [InlineKeyboardButton(text='Ликвидировать крысу', callback_data="kill_rat")]])
return_to_main = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Вернуться на главную', callback_data='return_home')]])