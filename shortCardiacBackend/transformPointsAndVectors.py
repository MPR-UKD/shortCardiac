import math

import numpy as np
from numba import jit


def line_intersection(line1, line2):
    """
    Calculates intersection of two lines

        Parameters:
            line1 (list): list with two points [point_1, point_2]
            line2 (list):  list with two points [point_1, point_2]

        Returns:
            intersection (tuple):(x, y)
    """
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        div = 1
    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y


@jit(nopython=True)
def get_vector(p0, p1):
    """
    Calculates the vector between two points, with len n = Number of dimensions

            Parameters:
                    p0 (np.array): np-array with shape (n,) - [d_1, d_2, d_3, ..., d_n]
                    p1 (np.array): np-array with shape (n,) - [d'_1, d'_2, d'_3, ..., d'_n]

            Returns:
                    p (np.array): np-array with shape (n,) - [d_1 - d'_1, d_2 - d'_2, d_3 - d'_3, ..., d_n - d'_n]
    """

    return p0 - p1


@jit(nopython=True)
def dotproduct(v1, v2):
    """
    Calculates dotproduct of two vectors

            Parameters:
                    v1 (np.array): vector as np-array with shape (n,) - [d_1, d_2, d_3, ..., d_n]
                    v2 (np.array): vector as np-array with shape (n,) - [d'_1, d'_2, d'_3, ..., d'_n]

            Returns:
                    dotproduct (float): v1 \dot v2
    """
    return (v1 * v2).sum()


@jit(nopython=True)
def length(v):
    """
    Calculates the length of vector v

            Parameters:
                    v (np.array): vect as np-array with shape (n,) - [d_1, d_2, d_3, ..., d_n]

            Returns:
                    length (float): ength of vector
    """
    scale = np.abs(v).sum()
    if scale == 0:
        return 0
    return np.sqrt(dotproduct(v/scale, v/scale))*scale


@jit(nopython=True)
def calc_angle(v1, v2):
    """
    Calculates the angle between two vectors in degree

            Parameters:
                    v1 (np.array): vector as np-array with shape (n,) - [d_1, d_2, d_3, ..., d_n]
                    v2 (np.array): vector as np-array with shape (n,) - [d'_1, d'_2, d'_3, ..., d'_n]

            Returns:
                    angle (float): angle in degree
    """
    length_v1 = length(v1)
    length_v2 = length(v2)
    if length_v1 == 0.0 or length_v2 == 0.0:
        return 1000
    value = dotproduct(v1/length_v1, v2/length_v2)
    return np.round(np.rad2deg(np.arccos(value)) * 1000) / 1000


def calc_center_of_2_points(p1, p2, mode='int'):
    """
    Returns center point between 2 points

            Parameters:
                    p1 (np.array): Point 1
                    p2 (np.array): Point 2
                    mode (str): Specifies if the midpoint should be exactly on one pixel or if subpixels are also possible

            returns:
                    center (np.array): Center point between p1 and p2
    """
    center = p1 + (p2 - p1) / 2
    if mode == 'int':
        return center.round().astype('int16')
    return center


def get_line(p1, p2, numpy=False):
    """
    Returns line with each point between 2 points

            Parameters:
                    p1 (np.array): Point 1
                    p2 (np.array): point 2
                    numpy (bool): Specifies whether line (list of points) should be determined as numpy array

            Returns:
                    line (list \ np. array): List with points between the two points
    """
    x1, y1 = p1.astype(np.int16)
    x2, y2 = p2.astype(np.int16)
    points = []
    issteep = abs(y2 - y1) > abs(x2 - x1)
    if issteep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    rev = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        rev = True
    deltax = x2 - x1
    deltay = abs(y2 - y1)
    error = round(deltax / 2)
    y = y1
    ystep = 1 if y1 < y2 else -1
    for x in range(x1, x2 + 1):
        if issteep:
            points.append((y, x))
        else:
            points.append((x, y))
        error -= deltay
        if error < 0:
            y += ystep
            error += deltax
    # Reverse the list if the coordinates were reversed
    if rev:
        points.reverse()
    if numpy:
        return np.array(points)
    return points


def rotate_points(points, origin, angle, mode='int'):
    """
    2D point transformation from a set of points around a clockwise origin.

            Parameters:
                    points (list): list of points (each point is an np.array)
                    origin (np.array): point around which the other points are rotated
                    angle (float): angle in degrees around which the points are rotated
                    mode (str): int or float - Specifies if points should be rotated to whole pixels only or if there should be subpixels

            Returns:
                    dcm_img (Pillow Image): dcm_image as RGB image
    """
    new_point_params = []
    if points is None:
        return new_point_params
    for point in points:
        if point is None:
            continue
        new_point_params.append(np.array(rotate_point(origin, point, angle, mode)))
    return new_point_params


@jit(nopython=True)
def rotate_point(origin, point, angle, mode='int'):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

            Parameters:
                origin (np.array) = origin
                point (np.array) = point for rotation
                angle (float) = angle in degree
                mode (str) = Specification whether the point should be rotated to a whole pixel only or whether there are subpixels

            Returns:
                point (np.array): point after rotation
    """
    angle = angle * math.pi / 180
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    if mode == 'int':
        return round(qx), round(qy)
    return qx, qy


def find_smallest_distance_to_ref(points, ref):
    """
    Returns the point from a set of points with the smallest distance to a reference point.

            Parameters:
                    points (list): List with points (points are available as np.array)
                    ref (np.array): Coordinates of the reference point

            Returns:
                    point (np.array): Nearest point
    """
    dist = [length(get_vector(np.array(p), ref)) for p in points]
    return points[np.argmin(dist)]


def find_distance_with_angles_and_fixed_point(points: list, angles: list, fixed_point: np.array):
    """
    Determines the maximum distances from a reference point to a contour (list of points) at different angles

            Parameters:
                    points (list): contour \ polygon as a list with points as np.array
                    angles (list): list with angles to be examined in degrees
                    fixed_point (np.array): coordinates of the reference point (x,y)

            returns:
                    distances (dict): Dictionary with the angle as key and the distances as a tuple with two coordinates
                    (point on contour, reference point)
    """
    D = {str(angle): None for angle in angles}
    for angle in angles:
        points_rot = [rotate_point(fixed_point, point, -angle) for point in points]
        if angle >= 0:
            points_rot = [point_rot if point_rot[1] > fixed_point[1] else np.array([-100, -100]) for point_rot in
                          points_rot]
        else:
            points_rot = [point_rot if point_rot[1] < fixed_point[1] else np.array([-100, -100]) for point_rot in
                          points_rot]
        delta_x = [abs(p[0] - fixed_point[0]) for p in points_rot]
        D[str(angle)] = [np.array(points[np.argmin(delta_x)]), np.array(fixed_point)]
    return D


def clean_points(points, key, mode='int'):
    """
     If there are multiple points with the same x-coordinate, all points that do not have the longest distance are removed.

            Parameters:
                    points (list): contour \ polygon as a list with points as np.array
                    key (str): x-coordinate
                    mode (str): coordinates of the reference point (x,y)

            Returns:
                    p1 (np.array): coordinates point 1
                    p2 (np.array): Coordinates point 2
                    length (float): Length between the two points
    """
    count = 0
    for p in points:
        if p is None:
            count += 1
    for _ in range(count):
        points.remove(None)
    if len(points) < 2:
        return None
    idx_min = np.argmax(np.array(points)[:, 1])
    idx_max = np.argmin(np.array(points)[:, 1])
    p1 = np.array(points[idx_min])
    p2 = np.array(points[idx_max])
    p1[0] = float(key)
    p2[0] = float(key)
    if mode == 'int':
        p1 = p1.round().astype('int16')
        p2 = p2.round().astype('int16')
    return p1, p2, length(get_vector(p1, p2))