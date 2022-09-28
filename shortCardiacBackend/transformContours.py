import itertools

import SimpleITK as sitk
import numpy as np
import pydicom
from PIL import Image, ImageDraw
from imantics import Mask
from numba import jit
from scipy.interpolate import splprep, splev
from skimage.transform import resize

from shortCardiacBackend.transformPointsAndVectors import find_smallest_distance_to_ref, clean_points, get_line, \
    rotate_points, length, get_vector, calc_center_of_2_points


def order_roi_to_dict(roi: list, delta: int = 1):
    """
    Sorting of points concerning x-coordinate

    :param roi: list of points as np.array
    :param delta: delta of x-values allowed to fill gaps and stabilize calculations concerning single contour points

    :return: point_dict_out (dict): Dictionary in which points are stored that have the same x-coordinate
    """
    point_dict = {}
    for point in roi:
        x_key = str(int(float(point[0])))
        if x_key not in point_dict.keys():
            point_dict[x_key] = [point]
        else:
            point_dict[x_key].append(point)
    point_dict_out = {}
    for key in point_dict.keys():
        points_list = []
        for i in range(-delta, delta + 1):
            points = point_dict.get(str(int(float(key)) + i))
            if points is not None:
                points_list += points
        point_dict_out[key] = clean_points(points_list, key)
    return point_dict_out


def smooth_coord_resizing(coords, resize_polygon_factor, smoothing=False, mode='int'):
    """
    Resizing and smoothing (using an approximating spline curve) the coordinates of a parameter.
    Notes: The function is implemented only for 2D calculations

            Parameters:
                    coords (np.array): Numpy array with the coordinates for a parameter (shape - (number of points,2))
                    resize_polygon_factor (int): Factor by which the coordinates are scaled up for a more accurate calculation
                    smoothing (bool): Specifies whether smoothing should be performed or only resizing should be performed.
                    Mode (str): Specifies whether only pixel coordinates (integers) or subpixel coordinates (float) should be used for the calculation.

            Returns:
                    coords (dict): Dictionary with all imported coordinates after resizing.
    """
    # If it is a parameter with only one point, no smoothing is performed, and the point is rescaled.
    coords = coords * resize_polygon_factor
    if coords.shape[0] != 1 and smoothing:
        x = coords[:, 0]
        y = coords[:, 1]
        d1 = (x.max() - x.min())
        d2 = (y.max() - y.min())
        # Approximation of the necessary pixels for an exact calculation of the parameters using the circumference of an ellipse
        number_of_points = (np.pi * (3 * (d1 + d2) / 2 - np.sqrt(d1 * d2))) / resize_polygon_factor
        tck, _ = splprep([x, y], s=0, per=True)
        xx, yy = splev(np.linspace(0, 1, round(number_of_points)), tck, der=0)
        coords = np.array([xx, yy]).transpose((1, 0))
    if mode == 'int':
        return coords.round().astype('int16')
    return coords


def coords_resizing(coords, resize_polygon_factor, smooth_resizing: bool = True, mode='int'):
    """
    Wrapper function calls the smooth_coord_resizing() function for all parameters found in coords.

            Parameters:
                    coords (dict): Dictionary in which all imported coordinates are stored.
                    resize_polygon_factor (int): Factor by which the coordinates are scaled up for a more accurate calculation
                    smooth_resizing (bool):
                    mode (str): Specifies whether only pixel coordinates (integers) or subpixel coordinates should be used for the calculation (float).

            change:
                    coords (dict): Dictionary with all imported coordinates after resizing
    """
    for key in coords.keys():
        coords[key] = smooth_coord_resizing(np.array(coords[key]), resize_polygon_factor, smooth_resizing, mode)


def find_ref_points(coords, config):
    right_ventricel = list(coords.get(config.rv_name_or_nr))
    left_ventricle = list(coords.get(config.lv_epi_name_or_nr))
    r_points, l_points = [], []
    min_delta = config.resize_polygon_factor
    count = 0
    while len(r_points) < 10:
        count += 1
        if count == 4:
            coords["sacardialRefPoint"] = None
            return None
        for p, q in itertools.product(right_ventricel, left_ventricle):
            l = length(get_vector(p, q))
            if l < min_delta:
                r_points.append(p)
                l_points.append(q)
        min_delta *= 2

    def calc_refpoints(points):
        distance, ref_points = [], []
        for p, q in itertools.product(points, points):
            distance.append(length(get_vector(p, q)))
            ref_points.append((p, q))
        ref = ref_points[np.nanargmax(distance)]
        if ref[0][1] > ref[1][1]:
            ref = (ref[1], ref[0])
        return ref

    l_ref = calc_refpoints(l_points)
    r_ref = calc_refpoints(r_points)
    coords["sacardialRefPoint"] = np.array([calc_center_of_2_points(np.array(l_ref[0]), np.array(r_ref[0]))])
    coords["sacardialInferiorRefPoint"] = np.array([calc_center_of_2_points(np.array(l_ref[1]), np.array(r_ref[1]))])


def correct_segmentations(coords, config):
    right_ventricel = list(coords.get(config.rv_name_or_nr))
    left_ventricle = list(coords.get(config.lv_epi_name_or_nr))

    # split left
    p1_l = find_smallest_distance_to_ref(left_ventricle, coords["sacardialRefPoint"])
    p2_l = find_smallest_distance_to_ref(left_ventricle, coords["sacardialInferiorRefPoint"])
    roi_1_l, roi_2_l = split_polygon(left_ventricle, p1_l, p2_l)

    # split right
    p1_r = find_smallest_distance_to_ref(right_ventricel, coords["sacardialRefPoint"])
    p2_r = find_smallest_distance_to_ref(right_ventricel, coords["sacardialInferiorRefPoint"])
    roi_1_r, roi_2_r = split_polygon(right_ventricel, p1_r, p2_r)

    def reverse_list(l):
        l.reverse()
        return l

    left_ventricle = roi_1_l + reverse_list(roi_2_r)

    coords[config.lv_epi_name_or_nr] = np.array(left_ventricle)

    coords["sarvendocardialContourVentral"] = np.array(roi_1_r)
    coords["sarvendocardialContourDorsal"] = np.array(roi_2_r)
    coords["sarvendocardialContourDorsalClosed"] = np.array(
        roi_2_r + list(get_line(coords["sacardialInferiorRefPoint"][0] / (0.5 * config.resize_polygon_factor),
                                coords["sacardialRefPoint"][0] / (0.5 * config.resize_polygon_factor), numpy=True) * 0.5 * config.resize_polygon_factor))


def split_polygon(points, p1, p2):
    """

    :param points:
    :param p1:
    :param p2:
    :return:
    """
    roi_1, roi_2, no_contour, current_contour = [], [], [], 'no_contour'
    roi_1_no_contour, roi_2_no_contour = [], []

    for p in points:
        if all(p == p1) and len(roi_2) == 0:
            if len(no_contour) > 0:
                no_contour.append(p)
            roi_1_no_contour = no_contour
            no_contour = []
            current_contour = 'roi_2'
            roi_2.append(p)
            continue

        if all(p == p2) and len(roi_1) == 0:
            if len(no_contour) > 0:
                no_contour.append(p)
            roi_2_no_contour = no_contour
            no_contour = []
            current_contour = 'roi_1'
            roi_1.append(p)
            continue
        if current_contour == 'roi_1':
            roi_1.append(p)
        if current_contour == 'roi_2':
            roi_2.append(p)
        if current_contour == 'no_contour':
            no_contour.append(p)

    roi_2 = roi_2 + roi_2_no_contour
    roi_1 = roi_1 + roi_1_no_contour

    l2 = calc_polygon_length(roi_2)
    l1 = calc_polygon_length(roi_1)
    if l1 > l2:
        return roi_1, roi_2
    return roi_2, roi_1


def calc_line_for_EI(roi, angle):
    """
    Calculation of the longest diameter along an angle for the analysis of the EI.
    Note: For more information, see Yamasaki et al - doi: ?????


            Parameters:
                    ROI (np.array): array in which the coordinates of a contour are stored - dimensions (numer_of_points, 2).
                    angle (float): angle to the heart axis along which the longest diameter is to be determined

            returns:
                    points (list): list of the two points defining the longest diameter [p1 (np.array), p2 (np.array)]
    """
    center = calc_center_of_polygon(roi)
    roi = rotate_points(roi, center, angle, 'int')
    point_dict = order_roi_to_dict(roi)
    xs = [int(float(key)) for key in point_dict.keys()]
    max_dist = 0
    line = None
    range_ = round((max(xs) - min(xs)) / 15)
    for i in range(min(xs) + range_, max(xs) - range_ + 1):
        dists = [point_dict[str(k)][2] if point_dict.get(str(k)) is not None else None for k in
                 range(i - range_, i + range_)]
        for _ in range(dists.count(None)):
            dists.remove(None)
        if len(dists) > 0:
            dist = np.array(dists).mean()

            if dist > max_dist:
                line = point_dict[str(i)][:2] if point_dict.get(str(i)) is not None else line
                max_dist = dist if point_dict.get(str(i)) is not None else max_dist
    return rotate_points(line, center, -angle)


@jit(nopython=True)
def calc_center_of_polygon(points):
    """
    Determines the centroid of a polygon

    :param points: 2D numpy array with points [(p1_x, p1_y),(p2_x, p2_y),...]

    :return: Array with the coordinates of the center point (x, y)
    """
    A = calc_area(list(points), False)
    x = points[:, 0]
    y = points[:, 1]
    n = len(points)
    xs = 0.0
    ys = 0.0
    for i in range(n):
        j = (i + 1) % n
        xs += (x[i] + x[j]) * (x[i] * y[j] - x[j] * y[i])
        ys += (y[i] + y[j]) * (x[i] * y[j] - x[j] * y[i])
    return np.array([round(xs / (6 * A)), round(ys / (6 * A))])


@jit(nopython=True)
def calc_area(corners, absolute=True):
    """
    Determines the area of a polygon

    :param corners: np.array of length n with the points of the respective ROI [(x1,y1),(x2,y2),...,(xn,yn)]
    :param absolute: Specifies whether there may also be negative surfaces

    :return: area (float): Area of contour
    """

    area = 0.0
    n = len(corners)
    for i in range(n):
        j = (i + 1) % n
        area += corners[i][0] * corners[j][1]
        area -= corners[j][0] * corners[i][1]
    area = area / 2.0
    if absolute:
        return abs(area)
    return area


def calc_polygon_length(points):
    """
    Determines the scope of a polygon

    :param points:  np.array of length n with the points of the respective ROI [(x1,y1),(x2,y2),...,(xn,yn)]

    :return: scope of a polygon as float
    """
    polygon_length = 0
    for i in range(len(points) - 1):
        polygon_length += length(get_vector(points[i], points[i + 1]))
    polygon_length += length(get_vector(points[0], points[-1]))
    return polygon_length


def smooth_3D_mask(mask, scaling=2):
    mask = resize(mask, (mask.shape[1] * scaling, mask.shape[0] * scaling), order=0)
    sitk_mask = sitk.GetImageFromArray(mask.astype('int8'))
    return sitk.GetArrayFromImage(sitk.BinaryDilate(sitk.BinaryMorphologicalClosing(sitk.BinaryErode(sitk_mask))))


def mask_to_polygon(mask):
    """
    calc polygon of binary mask

    :param mask: np.array as binary mask

    :return: polygon as numpy array
    """
    polygon = list(Mask(mask).polygons().points[0])

    def line_interp(points):
        inter_p = []
        for i in range(len(points)):
            j = 0 if i == len(points) - 1 else i + 1
            inter_p.append(points[i])
            inter_p.append(calc_center_of_2_points(points[i], points[j], mode='float'))
        return inter_p

    polygon = line_interp(line_interp(polygon))
    return np.array(polygon)


def calc_mask_of_polygon(dcm_file, coord, name, scaling_factor):
    """
    calculation of binary mask from polygon

    :param dcm_file: path to dicom file
    :param coord: dict with coords
    :param name: name / key for polygon in coord dict
    :param scaling_factor: int

    :return: binary numpy array
    """
    dcm_shape = pydicom.dcmread(dcm_file).pixel_array.shape
    img = Image.new('L', (dcm_shape[1] * scaling_factor, dcm_shape[0] * scaling_factor), 0)
    img_draw = ImageDraw.Draw(img)
    c = tuple([(c1 * scaling_factor, c2 * scaling_factor) for c1, c2 in list(coord.get(name))])
    img_draw.polygon(c, outline=1, fill=1)
    return np.array(img)
