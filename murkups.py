from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

btnTopUp = InlineKeyboardButton(text="Пополнить", callback_data="top_up")
topUpMenu = InlineKeyboardMarkup(row_width=1)
topUpMenu.insert(btnTopUp)

cansel_menu = InlineKeyboardMarkup(row_width=1)
cansel_menu.insert(InlineKeyboardButton(text="Отмена", callback_data="otmena"))


def buy_menu(isUrl=True, url="", bill=""):
    qiwiMenu = InlineKeyboardMarkup(row_width=1)
    if isUrl:
        btnUrlQiwi = InlineKeyboardButton(text="Оплатить", url=url)
        qiwiMenu.insert(btnUrlQiwi)

    btnCheckQiwi = InlineKeyboardButton(text="Проверить оплату", callback_data="check_" + bill)
    qiwiMenu.insert(btnCheckQiwi)

    return qiwiMenu
