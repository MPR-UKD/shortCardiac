import unittest
import numpy as np
from shortCardiacBackend.SIConvertion import *


class TestSIConvertion(unittest.TestCase):
    def test_convert_line_params(self):
        line_params = [(np.array([0, 0]), (np.array([10, 0])))]
        resize_factor = 10
        pixel_spacing = {"x": 1, "y": 1}
        self.assertEqual(line_to_si(line_params, resize_factor, pixel_spacing)[0], 1)

        line_params = [(np.array([0, 0]), (np.array([10, 0])))]
        resize_factor = 100
        pixel_spacing = {"x": 1, "y": 1}
        self.assertEqual(line_to_si(line_params, resize_factor, pixel_spacing)[0], 0.1)

        line_params = [(np.array([0, 0]), (np.array([10, 0])))]
        resize_factor = 10
        pixel_spacing = {"x": 2, "y": 2}
        self.assertEqual(line_to_si(line_params, resize_factor, pixel_spacing)[0], 2)

        line_params = [(np.array([0, 0]), (np.array([10, 0])))]
        resize_factor = 10
        pixel_spacing = {"x": 1, "y": 10}
        self.assertEqual(line_to_si(line_params, resize_factor, pixel_spacing)[0], 1)

        line_params = [(np.array([0, 0]), (np.array([10, 10])))]
        resize_factor = 10
        pixel_spacing = {"x": 1, "y": 1}
        self.assertEqual(
            line_to_si(line_params, resize_factor, pixel_spacing)[0], np.sqrt(2)
        )

    def test_area_to_si(self):
        area_params = [100]
        resize_factor = 10
        pixel_spacing = {"x": 1, "y": 1}
        self.assertEqual(area_to_si(area_params, resize_factor, pixel_spacing)[0], 1.0)

        area_params = [100]
        resize_factor = 10
        pixel_spacing = {"x": 1, "y": 2}
        self.assertEqual(area_to_si(area_params, resize_factor, pixel_spacing)[0], 2.0)

    def test_scope_to_si(self):
        scope_params = [4]
        resize_factor = 1
        pixel_spacing = {"x": 1, "y": 1}
        self.assertEqual(
            scope_to_si(scope_params, resize_factor, pixel_spacing)[0], 4.0
        )

        scope_params = [40]
        resize_factor = 10
        pixel_spacing = {"x": 1, "y": 1}
        self.assertEqual(
            scope_to_si(scope_params, resize_factor, pixel_spacing)[0], 4.0
        )

        scope_params = [4]
        resize_factor = 1
        pixel_spacing = {"x": 1, "y": 2}
        self.assertEqual(
            scope_to_si(scope_params, resize_factor, pixel_spacing)[0], 6.0
        )


if __name__ == "__main__":
    unittest.main()
