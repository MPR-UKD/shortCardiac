import unittest
from shortCardiacBackend.supportFunction import *


class TestsupportFunction(unittest.TestCase):

    def test_flatted_list(self):
        list_with_sublists = [[1, 2], [3]]
        self.assertEqual(flatted_list(list_with_sublists), [1, 2, 3])

if __name__ == '__main__':
    unittest.main()
