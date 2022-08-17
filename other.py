import os
import sqlite3
from docx2pdf import convert
from datetime import datetime
from aiogram.dispatcher.filters.state import State, StatesGroup


def now_time():
    return str(datetime.now().strftime("%d-%m %H:%M:%S> "))


class Database:
    def __init__(self, db_file):  # Инициализация базы данных
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def user_exists(self, user_id):  # Существует ли пользователь в БД
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `users` WHERE `user_id` = ?", (user_id,)).fetchall()
            return bool(len(result))

    def add_user(self, user_id):  # Добавление пользователя в БД
        with self.connection:
            return self.cursor.execute("INSERT INTO `users` (`user_id`) VALUES (?)", (user_id,))

    def user_money(self, user_id):  # Выборка баланса пользователя
        with self.connection:
            result = self.cursor.execute("SELECT `money` FROM `users` WHERE `user_id` = ?", (user_id,)).fetchmany(1)
            return float(result[0][0])

    def get_user_id(self, file_id):
        with self.connection:
            result = self.cursor.execute("SELECT `user_id` FROM `files` WHERE `file_id` = ?", (file_id,)).fetchmany(1)
            return int(result[0][0])

    def set_money(self, user_id, money):  # Установка баланса пользователю
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `money` = ? WHERE `user_id` = ?", (money, user_id,))

    def add_check(self, user_id, money, bill_id):  # Добавление чека в БД
        with self.connection:
            self.cursor.execute("INSERT INTO `check` (`user_id`, `money`, `bill_id`) VALUES (?,?,?)",
                                (user_id, money, bill_id,))

    def get_check(self, bill_id):  # Получение чека
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `check` WHERE `bill_id` = ?", (bill_id,)).fetchmany(1)
            if not bool(len(result)):
                return False
            return result[0]

    def delete_check(self, bill_id):  # Удаление чека
        with self.connection:
            return self.cursor.execute("DELETE FROM `check` WHERE `bill_id` = ?", (bill_id,))

    def add_file(self, user_id, file_path):  # Добавить файл пользователя в БД
        with self.connection:
            self.cursor.execute("INSERT INTO `files` (`user_id`, `file_path`) VALUES (?, ?)", (user_id, file_path,))
            file_id = self.cursor.execute("SELECT `file_id` FROM `files` WHERE `user_id` = ? ORDER BY `file_id` DESC",
                                          (user_id,)).fetchmany(1)

            if not file_path.endswith('.pdf'):
                new_file = "{0}_{2}.{1}".format(*file_path.rsplit('.', 1) + [str(file_id[0][0])])
                os.rename(file_path, new_file)
                print(now_time() + "Конвертация в .pdf")
                try:
                    convert(new_file)
                    print(now_time() + "Конвертация прошла успешно")
                    new_file_pdf = "{0}.pdf".format(*new_file.rsplit('.', 1))  # Ищем сконвертированный файл
                    os.remove(new_file)

                    self.cursor.execute("UPDATE `files` SET `file_path` = ? WHERE `file_id` = ?",
                                        (new_file_pdf, str(file_id[0][0]),))
                except ...:
                    print(now_time() + "Ошибка конвертации")

            return int(file_id[0][0])

    def set_status_pay(self, file_id, status):  # Изменить статус платежа по файлу
        with self.connection:
            return self.cursor.execute("UPDATE `files` SET `status_pay` = ? WHERE `file_id` = ?", (status, file_id,))

    def get_status_pay(self, file_id):
        with self.connection:
            result = self.cursor.execute("SELECT `status_pay` FROM `files` WHERE `file_id` = ?", (file_id,)).fetchmany(
                1)
            return bool(result[0][0])

    def set_status_print_confirm(self, file_id, status):  # Изменить статус печати файла
        with self.connection:
            return self.cursor.execute("UPDATE `files` SET `status_print` = ? WHERE `file_id` = ?",
                                       (status, file_id,))

    def get_status_print(self, file_id):
        with self.connection:
            result = self.cursor.execute("SELECT `status_print` FROM `files` WHERE `file_id` = ?",
                                         (file_id,)).fetchmany(1)
            return int(result[0][0])

    def set_status_printed(self, file_id, value):  # Изменить статус печати файла
        with self.connection:
            return self.cursor.execute("UPDATE `files` SET `print` = ?  WHERE `file_id` = ?", (value, file_id,))

    def not_pay_files(self, user_id):  # Возвращает выборку неоплаченных файлов пользователя
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM `files` WHERE `user_id` = ? AND `status_pay` = False AND `status_print` = TRUE",
                (user_id,)).fetchall()

            return result

    def not_print_files(self, user_id):  # Возвращает выборку оплаченных и не распечатаных файлов пользователя
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM `files` WHERE `user_id` = ? AND `status_pay` = TRUE AND `print` = FALSE",
                (user_id,)).fetchall()

            return result

    def file_exists(self, file_id):  # Существует ли файл  в БД
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `files` WHERE `file_id` = ?", (file_id,)).fetchall()
            return bool(len(result))

    def get_cost_file(self, file_id):
        with self.connection:
            result = self.cursor.execute("SELECT `cost` FROM `files` WHERE `file_id` = ?", (file_id,)).fetchmany(1)
            return float(result[0][0])

    def set_cost_file(self, file_id, price):
        with self.connection:
            return self.cursor.execute("UPDATE `files` SET `cost` = ?  WHERE `file_id` = ?", (price, file_id,))

    def get_file_name(self, file_id):
        with self.connection:
            result = self.cursor.execute("SELECT `file_path` FROM `files` WHERE `file_id` = ?", (file_id,)).fetchmany(1)
            return str('\\'.join(str(result[0][0]).split('\\')[-1:]))  # Кринж .-.

    def get_file_path(self, file_id):
        with self.connection:
            result = self.cursor.execute("SELECT `file_path` FROM `files` WHERE `file_id` = ?", (file_id,)).fetchmany(1)
            return str(result[0][0])


class FSM_payment(StatesGroup):
    money = State()
    file_id = State()
    reason = State()

# class Audit():
#     def __init__(self):
#         # Создать файл с текущей датой: novsuprintbot_08_08.log
#         pass
#     def log(self, message):
#         print(now_time(), message)
#         # И куда-то в файл будет писать-ся



