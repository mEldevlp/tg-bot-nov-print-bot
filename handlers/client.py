import os
import win32api
import win32print
import PyPDF2

from aiogram import types, Dispatcher
from createbot import dp, bot, GLOBAL_PATH, db, p2p, MAX_FILE_SIZE, ADMIN_CHAT_ID, PRICE_PER_PAGE
from keyboards import kb_client
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from other import FSM_payment, now_time
from datetime import datetime

import murkups
import random


class Audit:
    def __init__(self, message):
        date = datetime.now().strftime("%d-%m")
        if not os.path.isdir("logs"):
            os.mkdir("logs")
        file_name = f"logs/novprintbot-{date}.log"

        log_file = open(file_name, "w") if not os.path.isfile(file_name) else open(file_name, "a")

        log_message = now_time() + message + "\n"
        print(log_message)
        log_file.write(log_message)


def is_number(_str):
    try:
        int(_str)
        return True
    except ValueError:
        return False


def check_endswith(file: str):
    return True if file.endswith('.docx') or file.endswith('.doc') or file.endswith('.pdf') else False


# /start
async def command_start(message: types.Message):
    if not db.user_exists(message.from_user.id):
        db.add_user(message.from_user.id)

    await bot.send_message(message.from_user.id,
                           f"Бот печати документов.\nВаш баланс: {float(db.user_money(message.from_user.id))} ₽",
                           reply_markup=kb_client)
    await message.delete()


async def cm_start(message: types.Message):
    await message.delete()
    await FSM_payment.money.set()
    await bot.send_message(message.from_user.id, "Введите сумму для пополнения в рублях.",
                           reply_markup=murkups.cansel_menu)


async def get_money(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['money'] = float(message.text)
    msg_money = data['money']

    if is_number(msg_money):
        if msg_money >= 1:
            comment = str(message.from_user.id) + "_" + str(random.randint(1000, 9999))
            bill = p2p.bill(amount=msg_money, lifetime=3, comment=comment)

            db.add_check(message.from_user.id, msg_money, bill.bill_id)
            await bot.send_message(message.from_user.id,
                                   f"Вам нужно отправить {msg_money} ₽ на наш счёт QIWI по ссылке:"
                                   f"\n {bill.pay_url}\nВаш комментарий к оплате: {comment}",
                                   reply_markup=murkups.buy_menu(url=bill.pay_url, bill=bill.bill_id))
            await state.finish()
        else:
            await bot.send_message(message.from_user.id, "Минимальная сумма для пополнения 1 ₽")
    else:
        await bot.send_message(message.from_user.id, "Введите число.")


async def cansel_pay(callback: types.CallbackQuery, state: FSMContext):
    if await state.get_state() is None:
        return

    admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)

    for user in admins:
        if callback.from_user.id == user.user.id:
            await bot.send_message(ADMIN_CHAT_ID, "Действие отменено.")
            await state.finish()
            return

    await bot.send_message(callback.from_user.id, "Действие отменено.", reply_markup=kb_client)
    await state.finish()
    return


async def check(callback: types.CallbackQuery):
    bill = str(callback.data[6:])
    info = db.get_check(bill)

    if info:  # info != False
        if str(p2p.check(bill_id=bill).status) == "PAID":
            user_money = db.user_money(callback.from_user.id)
            money = int(info[2])  # 2 - это money в базе данных
            db.set_money(callback.from_user.id, user_money + money)
            await bot.send_message(ADMIN_CHAT_ID,
                                   f"Пользователь {callback.from_user.full_name}({callback.from_user.id})\n"
                                   f"пополнил баланс на {money} ₽\n"
                                   f"Его баланс: {float(db.user_money(callback.from_user.id))} ₽")

            await bot.send_message(callback.from_user.id, "Ваш счёт пополнен! Напишите /start")
            db.delete_check(bill_id=bill)
        else:
            await bot.send_message(callback.from_user.id, "Вы не оплатили счёт",
                                   reply_markup=murkups.buy_menu(False, bill=bill))
    else:
        await bot.send_message(callback.from_user.id, "Счёт не найден.")


def getfilename(file: str):
    return str('\\'.join(str(file).split('\\')[-1:]))


async def pay_file(callback: types.CallbackQuery):
    file_id = str(callback.data[9:])
    user_id = db.get_user_id(file_id)
    user_money = db.user_money(user_id)
    cost_file = db.get_cost_file(file_id)

    user = await bot.get_chat_member(user_id, user_id)
    full_name = user.user.full_name
    if user_money > cost_file:
        db.set_money(user_id, round(user_money - cost_file, 1))
        db.set_status_pay(file_id, True)
        file_name = db.get_file_name(file_id)
        new_user_money = db.user_money(user_id)
        await bot.send_message(user_id, f"Файл [{file_name}] успешно оплачен.\n"
                                        f"Ваш баланс: {new_user_money} ₽",
                               reply_markup=kb_client)

        await bot.send_message(ADMIN_CHAT_ID, f"Пользователь {full_name} оплатил файл:\n"
                                              f"[{file_name}]\n"
                                              f"Его баланс: {new_user_money} ₽")

    else:
        await bot.send_message(user_id, "У вас недостаточно средств. Пополните баланс", reply_markup=kb_client)


async def command_purchase(message: types.Message):
    records = db.not_pay_files(message.from_user.id)
    id_file = []
    not_paid_files = []
    cost_file = []
    count_of_rec = 0

    for data in records:
        id_file.append(str(data[0]))
        not_paid_files.append(getfilename(data[2]))
        cost_file.append(str(data[5]))
        count_of_rec += 1

    if count_of_rec >= 1:
        pay_files_menu = InlineKeyboardMarkup(row_width=1)

        for i in range(count_of_rec):
            btn = InlineKeyboardButton(text=id_file[i] + " - " + not_paid_files[i] + " - " + cost_file[i] + " ₽",
                                       callback_data="pay_file_" + str(id_file[i]))
            pay_files_menu.insert(btn)

        await bot.send_message(message.from_user.id, f"Одобренные файлы для оплаты", reply_markup=pay_files_menu)
        await message.delete()
    else:
        await bot.send_message(message.from_user.id, f"Одобренных файлов не найдено.", reply_markup=kb_client)
        await message.delete()


async def command_info(message: types.Message):
    await bot.send_message(message.from_user.id, 'Информация по боту...', reply_markup=kb_client)
    await message.delete()


async def command_help(message: types.Message):
    await bot.send_message(message.from_user.id, 'Помощь...', reply_markup=kb_client)
    await message.delete()


async def command_print_file(message: types.Message):
    records = db.not_print_files(message.from_user.id)
    id_file = []
    not_printed_files = []
    cost_file = []
    count_of_rec = 0

    for data in records:
        id_file.append(str(data[0]))
        not_printed_files.append(getfilename(data[2]))
        cost_file.append(str(data[5]))
        count_of_rec += 1

    if count_of_rec >= 1:
        pay_files_menu = InlineKeyboardMarkup(row_width=1)

        for i in range(count_of_rec):
            btn = InlineKeyboardButton(text=f"{id_file[i]} - {not_printed_files[i]} - {cost_file[i]} ₽",
                                       callback_data=f"print_file_{id_file[i]}")
            pay_files_menu.insert(btn)

        await bot.send_message(message.from_user.id, "Оплаченные файлы для печати:", reply_markup=pay_files_menu)
        await message.delete()
    else:
        await bot.send_message(message.from_user.id, "Оплаченных файлов не найдено.", reply_markup=kb_client)
        await message.delete()


async def print_file(callback: types.CallbackQuery):
    file_id = str(callback.data[11:])
    user_id = db.get_user_id(file_id)
    file_name = db.get_file_name(file_id)
    file_path = db.get_file_path(file_id)

    user = await bot.get_chat_member(user_id, user_id)

    await bot.send_message(ADMIN_CHAT_ID,
                           f"[{user.user.full_name}](tg://user?id={user_id}) запустил принтер на печать\nФайл - "
                           f"*[{file_name}]*\n*ID - {file_id}*", parse_mode="Markdown")

    Audit(f'Попытка печати файла {file_path}')

    try:
        win32api.ShellExecute(0, "print", file_path, "%s" % win32print.GetDefaultPrinter(), ".", 0)
        Audit(f'[{file_name}] был распечатан')
        # db.set_status_printed(file_id, True)

    except Exception.args:
        Audit("Что-то пошло не так. файл не распечатан")


def word_convert(arr):
    out = []
    for file in arr:
        if '.docx' or '.doc' in file:
            out.append(file)
    return out


def get_file_price(file_id):
    url = db.get_file_path(file_id)
    num_pages = PyPDF2.PdfFileReader(url).pages
    return len(num_pages)


async def handle_docs(message: types.Message):
    file = message.document.file_name
    userfullname = message.from_user.full_name
    userid = message.from_user.id
    file_size = message.document.file_size

    Audit(f'Пользователь {userfullname}({userid}) Загрузил файл - [{file}]({file_size} Bytes)')

    destination_file = f'{GLOBAL_PATH}.receive_files\\users\\{userfullname}\\{file}'
    try:
        Audit('Осуществляется попытка скачивания файла...')

        if file_size > MAX_FILE_SIZE:  # MAX_FILE_SIZE = 104 857 600
            await bot.send_message(userid,
                                   "❌Файл не принят❌\nСлишком большой размер."
                                   "\nНеобходимо загружать файлы размер которых меньше 100 МБ!")

            Audit('Скачивание отменено. Слишком большой файл.')
        elif check_endswith(file):
            Audit('Скачивание...')
            await message.document.download(destination_file)
            Audit(f'Файл {file}({file_size} Bytes) успешно скачан.')

            await bot.send_message(userid, "✅ Файл принят на проверку✅\n⏳Ожидайте одобрения администратора⏳")

            file_id = db.add_file(userid, destination_file)

            admin_file_menu = InlineKeyboardMarkup(row_width=1)
            admin_btn_confirm = InlineKeyboardButton(text=f"✅ Одобрить [{file_id}] ✅",
                                                     callback_data="confirm_" + str(file_id))

            admin_btn_cansel = InlineKeyboardButton(text=f"❌ Отклонить [{file_id}] ❌",
                                                    callback_data="cansel_" + str(file_id))

            admin_file_menu.insert(admin_btn_confirm)
            admin_file_menu.insert(admin_btn_cansel)

            price = get_file_price(file_id) * PRICE_PER_PAGE

            db.set_cost_file(file_id, price)
            file_path = db.get_file_path(file_id)
            # file_name = db.get_file_name(file_id)

            await bot.send_document(ADMIN_CHAT_ID, open(file_path, 'rb'),
                                    caption=f"*{userid}*\n[{userfullname}](tg://user?id={userid})\n"
                                            f"*Стоимость - {price} ₽*",
                                    parse_mode="Markdown", reply_markup=admin_file_menu)
        else:
            Audit('Скачивание отменено. Расширение файла не верное.')
            await bot.send_message(userid, "Расширение файла не правильное!\n Загрузите *.docx, *.doc, *.pdf")
    except ...:
        await bot.send_message(userid, "❌ Файл не принят ❌\nОшибка скачивания!")
        Audit('Ошибка скачивания!')


async def confirm_file(callback: types.CallbackQuery):
    file_id = str(callback.data[8:])

    if not db.file_exists(file_id):
        await bot.send_message(ADMIN_CHAT_ID,
                               f"Файла с ID - ({file_id}) не существует.\nПроверьте свой запрос.")
        return

    if db.get_status_print(file_id) == 1:
        await bot.send_message(ADMIN_CHAT_ID, f"Этот файл[{file_id}] уже одобрен.")

    elif db.get_status_print(file_id) == -1:
        await bot.send_message(ADMIN_CHAT_ID, f"Одобрение невозможно, т.к. этот файл[{file_id}] отклонён.")

    else:
        file_name = db.get_file_name(file_id)
        user_id = db.get_user_id(file_id)
        db.set_status_print_confirm(file_id, True)
        price = db.get_cost_file(file_id)

        await bot.send_message(user_id, f"✅ Файл [{file_name}] одобрен ✅\nЦена распечатки: {price} ₽")
        await bot.send_message(ADMIN_CHAT_ID,
                               f"Файл [{file_name}]({file_id}) был одобрен.\nЦена распечатки - {price} ₽\n"
                               f"Пользователь уведомлён.")


async def cansel_file(callback: types.CallbackQuery, state: FSMContext):
    file_id = str(callback.data[7:])

    await FSM_payment.reason.set()

    async with state.proxy() as data:
        data['file_id'] = file_id

    if not db.file_exists(file_id):
        await bot.send_message(ADMIN_CHAT_ID,
                               f"Файла с ID - ({file_id}) не существует.\nПроверьте свой запрос.")
        await state.finish()
        return

    if db.get_status_print(file_id) == 1:
        await bot.send_message(ADMIN_CHAT_ID, f"Отклонение невозможно, т.к. этот файл[{file_id}] одобрен.")
        await state.finish()
    elif db.get_status_print(file_id) == -1:
        await bot.send_message(ADMIN_CHAT_ID, f"Этот файл[{file_id}] уже отклонён.")
        await state.finish()
    else:
        await bot.send_message(ADMIN_CHAT_ID, f"Введите причину отказа - [{file_id}]",
                               reply_markup=murkups.cansel_menu)


async def cansel_file_set_reason(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['reason'] = message.text
    await message.delete()

    file_id = data['file_id']
    reason = data['reason']

    user_id = db.get_user_id(file_id)
    file_name = db.get_file_name(file_id)
    db.set_status_print_confirm(file_id, -1)

    await bot.send_message(user_id, f"❌ Файл [{file_name}] был отклонён ❌\nПричина:\n\"" + reason + "\"")
    await bot.send_message(ADMIN_CHAT_ID,
                           f"Файл [{file_name}]({file_id}) был отклонён.\nПричина: {reason}\n"
                           f"Файл удалён.\nПользователь уведомлён.")
    os.remove(db.get_file_path(file_id))

    await state.finish()


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(command_start, Text(equals='Начать', ignore_case=True))
    dp.register_message_handler(command_start, Text(equals='💰 Баланс 💰', ignore_case=True))
    dp.register_message_handler(command_start, Text(equals='/start', ignore_case=True))
    dp.register_message_handler(command_start, Text(equals='Запустить', ignore_case=True))
    dp.register_message_handler(cm_start, Text(equals='💳 Пополнить 💳', ignore_case=True), state=None)
    dp.register_message_handler(get_money, state=FSM_payment.money)
    dp.register_message_handler(command_purchase, Text(equals='💵 Оплатить 💵', ignore_case=True))
    dp.register_message_handler(command_info, Text(equals='📃 Инфо 📃', ignore_case=True))
    dp.register_message_handler(command_help, Text(equals='🆘 Помощь 🆘', ignore_case=True))
    dp.register_message_handler(command_print_file, Text(equals='🖨 Распечатать 🖨', ignore_case=True))
    dp.register_callback_query_handler(print_file, text_contains="print_file_")
    dp.register_message_handler(handle_docs, content_types=types.ContentType.DOCUMENT)
    dp.register_callback_query_handler(cansel_pay, text_contains="otmena", state="*")
    dp.register_callback_query_handler(check, text_contains="check_")
    dp.register_callback_query_handler(pay_file, text_contains="pay_file_")
    dp.register_callback_query_handler(confirm_file, text_contains="confirm_")
    # dp.register_message_handler(confirm_file_set_price, state=FSM_payment.price)
    dp.register_callback_query_handler(cansel_file, text_contains="cansel_")
    dp.register_message_handler(cansel_file_set_reason, state=FSM_payment.reason)
