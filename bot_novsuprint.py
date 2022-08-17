import os

from aiogram.utils import executor
from createbot import dp, bot, ADMIN_CHAT_ID
from other import now_time
from handlers import client


async def on_startup(_):
    os.system("cls")
    print(now_time() + "--- Бот инициализирован ---")
    # await bot.send_message(ADMIN_CHAT_ID, "Бот включён ✅")



async def on_shutdown(_):
    print(now_time() + '--- Бот выключился ---')
    await bot.send_message(ADMIN_CHAT_ID, "Бот выключился ❌")


client.register_handlers_client(dp)
executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
