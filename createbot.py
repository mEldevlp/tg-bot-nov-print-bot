import os

from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from other import Database
from pyqiwip2p import QiwiP2P


storage = MemoryStorage()
p2p = QiwiP2P(auth_key=os.getenv('QIWI_TOKEN'))
GLOBAL_PATH = os.getenv('GLOBAL_PATH')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
MAX_FILE_SIZE = 104857600  # 104 857 600 Байтов
PRICE_PER_PAGE = 5

db = Database("datastorage.db")
bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot, storage=storage)
