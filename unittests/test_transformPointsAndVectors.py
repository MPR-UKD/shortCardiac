import unittest

import numpy as np

from shortCardiacBackend.transformPointsAndVectors import *


class Test_transformPointsAndVectors(unittest.TestCase):
    def test_line_intersection(self):
        line1 = [np.array([0, 0]), np.array([0, 10])]
        line2 = [np.array([0, 0]), np.array([0, 20])]
        self.assertEqual(line_intersection(line1, line2), (0.0, 0.0))

        line1 = [np.array([0, 0]), np.array([10, 10])]
        line2 = [np.array([0, 10]), np.array([10, 0])]
        self.assertEqual(line_intersection(line1, line2), (5.0, 5.0))

    def test_get_vector(self):
        p1 = np.array([0, 0])
        p2 = p1
        self.assertTrue(all(get_vector(p1, p2) == np.array([0, 0])))

        p1 = np.array([10, 10])
        p2 = p1
        self.assertTrue(all(get_vector(p1, p2) == np.array([0, 0])))

        p1 = np.array([0, 0])
        p2 = np.array([10, 10])
        self.assertTrue(all(get_vector(p1, p2) == np.array([-10, -10])))

    def test_dot_product(self):
        v1 = np.array([0, 0])
        v2 = v1
        self.assertEqual(dotproduct(v1, v2), 0)

        v1 = np.array([0, 1])
        v2 = np.array([0, 1])
        self.assertEqual(dotproduct(v1, v2), 1)

        v1 = np.array([0, 0])
        v2 = np.array([0, 1])
        self.assertEqual(dotproduct(v1, v2), 0)

        v1 = np.array([7, 2])
        v2 = np.array([3, 6])

        # v1 dot v2 = v1_x * v2_x + v1_y * v2_y
        #           = 7 * 3 + 2 * 6
        #           = 33
        self.assertEqual(dotproduct(v1, v2), 33)

    def test_length(self):
        v1 = np.array([0, 0])
        self.assertEqual(length(v1), 0)

        v1 = np.array([0, 1])
        self.assertEqual(length(v1), 1)

        v1 = np.array([0, 10])
        self.assertEqual(length(v1), 10)

        v1 = np.array([10, 10])
        self.assertEqual(length(v1), math.sqrt(10**2 + 10**2))

    def test_calc_angle(self):
        v1 = np.array([0, 1])
        v2 = np.array([1, 0])
        self.assertEqual(calc_angle(v1, v2), 90.0)

        v1 = np.array([0, 1])
        v2 = np.array([1, 1])
        self.assertEqual(calc_angle(v1, v2), 45.0)

        v1 = np.array([0, 0])
        v2 = np.array([1, 1])
        # Hint: 1000 is default value
        self.assertEqual(calc_angle(v1, v2), 1000)

    def test_calc_center_of_2_points(self):
        p1 = np.array([0, 0])
        p2 = np.array([0, 0])
        self.assertTrue(all(calc_center_of_2_points(p1, p2) == np.array([0, 0])))

        p1 = np.array([0, 10])
        p2 = np.array([0, 0])
        self.assertTrue(all(calc_center_of_2_points(p1, p2) == np.array([0, 5])))

        p1 = np.array([0, 0])
        p2 = np.array([2, 2])
        self.assertTrue(all(calc_center_of_2_points(p1, p2) == np.array([1, 1])))

    def test_get_line(self):
        p1 = np.array([0, 0])
        p2 = np.array([0, 0])
        self.assertEqual(get_line(p1, p2)[0], (0, 0))

        p1 = np.array([0, 0])
        p2 = np.array([0, 1])
        self.assertEqual(get_line(p1, p2)[0], (0, 0))
        self.assertEqual(get_line(p1, p2)[1], (0, 1))

        p1 = np.array([0, 0])
        p2 = np.array([0, 2])
        self.assertEqual(get_line(p1, p2)[1], (0, 1))

        p1 = np.array([0, 0])
        p2 = np.array([2, 2])
        self.assertEqual(get_line(p1, p2)[1], (1, 1))


if __name__ == "__main__":
    unittest.main()
