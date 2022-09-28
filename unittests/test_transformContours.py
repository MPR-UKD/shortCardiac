import unittest

import numpy as np

from shortCardiacBackend.transformContours import *


class Test_transformContours(unittest.TestCase):

    def test_order_roi_to_dict(self):
        roi = [np.array([0, 0]), np.array([0, 10]), np.array([100, 100])]
        delta = 1
        results_ = order_roi_to_dict(roi, delta)['0']
        self.assertTrue(any([(np.array([0, 0]) == _).all() for _ in results_]))
        self.assertTrue(any([(np.array([0, 10]) == _).all() for _ in results_]))
        self.assertFalse(any([(np.array([100, 100]) == _).all() for _ in results_]))

    def test_calc_center_of_polygon(self):
        points = np.array([(0, 0), (0, 10), (10, 10), (10, 0)])
        self.assertTrue((calc_center_of_polygon(points) == np.array((5, 5))).all())

    def test_calc_area(self):
        points = np.array([(0, 0), (0, 10), (10, 10), (10, 0)])
        self.assertEqual(calc_area(points), 100.0)

    def test_calc_polygon_length(self):
        points = np.array([(0, 0), (0, 10), (10, 10), (10, 0)])
        self.assertEqual(calc_polygon_length(points), 40.0)

    def test_mask_to_polygon(self):
        mask = np.zeros((10, 10))
        mask[2:8, 2:8] = 1
        polygon = mask_to_polygon(mask)
        self.assertEqual(polygon.__class__, np.ndarray)
        # TODO: So far only visually checked, think about how to implement a unittest for this purpose


if __name__ == '__main__':
    unittest.main()
