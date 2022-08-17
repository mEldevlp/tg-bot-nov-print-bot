from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

b1 = KeyboardButton('💵 Оплатить 💵')
b2 = KeyboardButton('🖨 Распечатать 🖨')
b3 = KeyboardButton('📃 Инфо 📃')
b4 = KeyboardButton('🆘 Помощь 🆘')
b5 = KeyboardButton('💰 Баланс 💰')
b6 = KeyboardButton('💳 Пополнить 💳')

kb_client = ReplyKeyboardMarkup(resize_keyboard=True)
kb_client.add(b1).add(b2).row(b3, b4).row(b5, b6)
