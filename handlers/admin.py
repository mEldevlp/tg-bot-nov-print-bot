from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from createbot import dp, bot, GLOBAL_PATH, db


async def command_admin(message: types.Message):
    msg_admin = message.text
    file_id = ""
    price = 0
    i = 0

    if msg_admin[:8] == "Одобрить":  # Одобрить 15 40
        buffer = msg_admin[9:]
        while buffer[i] != " ":
            file_id += buffer[i]
            i += 1
        price = buffer[i:]

        user_id = db.get_user_id(file_id)
        await bot.send_message(user_id, f"Ваш файл одобрен!\n Цена распечатки: {price} руб.")

    elif msg_admin[9:] == "Отклонить":  # Отклонить 15 Ты прислал чёрный лист!
        buffer = msg_admin[10:]
        reason = ""
        while buffer[i] != " ":
            file_id += buffer[i]
            i += 1

        reason = buffer[i+1:]
        user_id = db.get_user_id(file_id)
        await bot.send_message(user_id, "Ваш файл был отклонён! Причина:\n\""+reason+"\"")
        # Отклонённый файл будет удалятся с бд
        # db.delete_file(file_id)

def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(command_admin, is_chat_admin=True)
