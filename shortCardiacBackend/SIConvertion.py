import numpy as np
from shortCardiacBackend.transformPointsAndVectors import length, get_vector


def convert_params(
    line_params: list,
    point_params: list,
    area_params: list,
    scope_params: list,
    resize_factor: int,
    pixel_spacing: dict,
):
    """
    wrapper function to convert als params from pixel spacing to "SI" units

    :param line_params: list with tuples (point1, point2) which define a line
    :param point_params: list with points as numpy array
    :param area_params: list with areas as floats
    :param scope_params: list with scopes as floats
    :param resize_factor: resizing factor between coordinates and dicom pixel
    :param pixel_spacing: dict with keys 'x' and 'y' which load from DICOM pixel spacing

    :return: line_params, point_params, area_paras, scope_params after convertation to "SI" units
    """
    line_params = line_to_si(line_params, resize_factor, pixel_spacing)
    point_params = point_without_resizing(point_params, resize_factor)
    area_params = area_to_si(area_params, resize_factor, pixel_spacing)
    scope_params = scope_to_si(scope_params, resize_factor, pixel_spacing)
    return line_params, point_params, area_params, scope_params


def point_without_resizing(params, resize_factor):
    if params is not None:
        return [(x / resize_factor, y / resize_factor) for x, y in params]


def line_to_si(params: list, resize_factor: int, pixel_spacing: dict):
    """
    convert line params from pixel spacing to "SI" unit - millimeter

    :param params: list with tuples (point1, point2) which define a line
    :param resize_factor: resizing factor between coordinates and dicom pixel
    :param pixel_spacing: dict with keys 'x' and 'y' which load from DICOM pixel spacing

    :return: line_params as list of floats (length in mm)
    """
    if params is not None:
        return [
            length(
                get_vector(
                    np.array(
                        [
                            p[0] / resize_factor * pixel_spacing["x"],
                            p[1] / resize_factor * pixel_spacing["y"],
                        ]
                    ),
                    np.array(
                        [
                            q[0] / resize_factor * pixel_spacing["x"],
                            q[1] / resize_factor * pixel_spacing["y"],
                        ]
                    ),
                )
            )
            for p, q in params
        ]


def area_to_si(area_params: list, resize_factor: int, pixel_spacing: dict):
    """
    convert area params from pixel spacing to "SI" unit - millimeter ** 2

    :param area_params: list with areas as floats
    :param resize_factor: resizing factor between coordinates and dicom pixel
    :param pixel_spacing: dict with keys 'x' and 'y' which load from DICOM pixel spacing

    :return: list with area_params as list of floats with SI units - mm^2
    """
    if area_params is not None:
        return [
            area / (resize_factor**2) * pixel_spacing["x"] * pixel_spacing["y"]
            for area in area_params
        ]


def scope_to_si(scope_params, resize_factor, pixel_spacing):
    """

    :param scope_params: list with scopes as floats
    :param resize_factor: resizing factor between coordinates and dicom pixel
    :param pixel_spacing: dict with keys 'x' and 'y' which load from DICOM pixel spacing

    :return:
    """
    if scope_params is not None:
        return [
            scope / resize_factor * (pixel_spacing["x"] + pixel_spacing["y"]) / 2
            for scope in scope_params
        ]
