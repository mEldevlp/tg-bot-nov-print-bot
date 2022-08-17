# import unittest
# from other import *
#
#
# class TestBotFunctional(unittest.TestCase):
#     def test_user_exists(self):
#         db = Database("datastorage.db")
#         self.assertEqual(db.user_exists("2114464762"), True)
#
#     def test_user_exists2(self):
#         db = Database("datastorage.db")
#         self.assertEqual(db.user_exists("13372281488"), False)


def last_digit(n1, n2):
    return pow(n1, n2, 10)


if __name__ == '__main__':  # 7
    print(last_digit(10, 15 ** 12))
