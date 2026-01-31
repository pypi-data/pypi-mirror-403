import unittest
from f_bomb import F_Bomb


class test_f_bomb(unittest.TestCase):
    def test_f_bomb(self):
        the_bomb = F_Bomb()
        self.assertEqual(str(the_bomb), "FUCK!")

    def test_language(self):
        the_bomb = F_Bomb()
        self.assertEqual(the_bomb.drop(), "FUCK!")
        self.assertEqual(the_bomb.drop("FR"), "PUTAIN!")
        self.assertEqual(the_bomb.drop("de"), "SCHEISSE!")


if __name__ == '__main__':
    unittest.main()
