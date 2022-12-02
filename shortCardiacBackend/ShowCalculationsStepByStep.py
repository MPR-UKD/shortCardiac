import os
from copy import deepcopy

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from shortCardiacBackend.visualisation import concatenate_images, plot_img

# Can be manually adjusted here
show_calculation_step_by_step_folder = r"."


def init(dicom: np.ndarray, coords: dict):
    # necessary because coords is a dict which works in python as pointer
    return deepcopy(dicom), deepcopy(coords)


def get_img(dicom_img: np.ndarray):
    img_poly = Image.new("RGBA", dicom_img.size)
    img = ImageDraw.Draw(img_poly, "RGBA")
    dicom_img = dicom_img.convert("RGBA")
    return img, img_poly, dicom_img


def resize(dicom_img: np.ndarray, coords: dict, factor: int):
    for key in coords.keys():
        coords[key] = factor * coords[key]
    dicom_img = dicom_img.resize(tuple((np.array(dicom_img.size[:2]) * factor)))
    return dicom_img, coords


def show_Ref_points_and_septum_axis(dicom_img: np.ndarray, coords: dict):
    dicom_img, coords = init(dicom_img, coords)
    dicom_img, coords = resize(dicom_img, coords, 4)
    img, img_poly, dicom_img = get_img(dicom_img)

    p = tuple(
        [
            (p1, p2)
            for p1, p2 in [
                coords["sacardialRefPoint"][0],
                coords["sacardialInferiorRefPoint"][0],
            ]
        ]
    )
    img.line(p, fill="red", width=8)
    points = ["P1", "P2"]
    font = ImageFont.truetype("arial.ttf", 150)

    for i in range(2):
        circle_size = 45
        img.ellipse(
            (
                p[i][0] - circle_size,
                p[i][1] - circle_size,
                p[i][0] + circle_size,
                p[i][1] + circle_size,
            ),
            outline="red",
            width=8,
        )
        img.text((p[i][0] + 50, p[i][1]), points[i], font=font, fill="red")
    dicom_img.paste(img_poly, mask=img_poly)

    center = ((p[1][0] - p[0][0]) / 2 + p[0][0], (p[1][1] - p[0][1]) / 2 + p[0][1])
    x, y = center[0], center[1]
    h, w = dicom_img.size
    h = round(0.25 * h)
    w = round(0.25 * w)
    dicom_img = dicom_img.crop([x - w, y - h, x + w, y + h])
    dicom_img.save(show_calculation_step_by_step_folder + os.sep + "Ref_points.png")


def show_coord_correction(dicom_img, coords2, coords, config):
    dicom_img, coords = init(dicom_img, coords)

    p = tuple(
        [
            (p1, p2)
            for p1, p2 in [
                coords["sacardialRefPoint"][0],
                coords["sacardialInferiorRefPoint"][0],
            ]
        ]
    )

    center = ((p[1][0] - p[0][0]) / 2 + p[0][0], (p[1][1] - p[0][1]) / 2 + p[0][1])
    x, y = center[0], center[1]
    h, w = dicom_img.size
    h = round(0.15 * h)
    w = round(0.15 * w)

    dicom_img = Image.new("RGBA", dicom_img.size, color="white")
    _, coords2 = init(dicom_img, coords2)

    _, coords = resize(dicom_img, coords, 1)
    dicom_img, coords = resize(dicom_img, coords2, 1)

    d = {}
    for ii, coord in enumerate([coords, coords2]):
        coord = [
            coords.get(config.lv_epi_name_or_nr),
            coords.get(config.lv_endo_name_or_nr),
            coords.get(config.rv_name_or_nr),
        ]
        img, img_poly, dicom_img_temp = get_img(dicom_img)
        a = 50
        colors = [(0, 0, 100, a), (0, 100, 0, a), (100, 0, 0, a), (100, 100, 100, a)]

        for i, c in enumerate(coord):
            if c is None:
                continue
            c = tuple([(c1, c2) for c1, c2 in c])
            try:
                color_a = colors[i]
                color_a = (color_a[0], color_a[1], color_a[2], 250)
                img.polygon(c, fill=colors[i], outline=color_a, width=2)
            except:
                pass
        dicom_img_temp.paste(img_poly, mask=img_poly)
        dicom_img = dicom_img_temp.crop([x - w, y - h, x + w, y + h])
        d[str(ii)] = dicom_img_temp
    dicom = concatenate_images(d["0"], d["1"])
    dicom.save(show_calculation_step_by_step_folder + os.sep + "CordCorrection.png")


def show_angle(dcm_img_pre, coords_pre, dcm_img_post, coords_post, angle):
    dcm_img_pre, coords_pre = init(dcm_img_pre, coords_pre)
    dcm_img_pre, coords_pre = resize(dcm_img_pre, coords_pre, 4)
    img_pre, img_poly_pre, dcm_img_pre = get_img(dcm_img_pre)

    dcm_img_post, coords_post = init(dcm_img_post, coords_post)
    dcm_img_post, coords_post = resize(dcm_img_post, coords_post, 4)
    img_post, img_poly_post, dcm_img_post = get_img(dcm_img_post)

    h, w = dcm_img_pre.size
    h = round(0.25 * h)
    w = round(0.25 * w)

    def plot(img, coords, img_poly, dicom_img, angle):
        p = tuple(
            [
                (p1, p2)
                for p1, p2 in [
                    coords["sacardialRefPoint"][0],
                    coords["sacardialInferiorRefPoint"][0],
                ]
            ]
        )
        center = ((p[1][0] - p[0][0]) / 2 + p[0][0], (p[1][1] - p[0][1]) / 2 + p[0][1])
        x = center[0]
        y = center[1]
        circle_size = abs(p[1][1] - p[0][1])
        if angle != 0:
            if angle < 0:
                img.arc(
                    (
                        p[1][0] - circle_size,
                        p[1][1] - circle_size,
                        p[1][0] + circle_size,
                        p[1][1] + circle_size,
                    ),
                    270,
                    270 - angle,
                    fill=(0, 250, 0, 50),
                    width=circle_size,
                )
            else:
                img.arc(
                    (
                        p[1][0] - circle_size,
                        p[1][1] - circle_size,
                        p[1][0] + circle_size,
                        p[1][1] + circle_size,
                    ),
                    270 - angle,
                    270,
                    fill=(0, 250, 0, 50),
                    width=circle_size,
                )

        p2 = ((p[1][0], p[1][1] + 300), (p[1][0], p[0][1] - 300))
        img.line(p2, fill="blue", width=8)
        img.line(p, fill="red", width=8)

        dicom_img.paste(img_poly, mask=img_poly)
        dicom_img = dicom_img.crop([x - w, y - h, x + w, y + h])

        return dicom_img

    dcm_img_pre = plot(img_pre, coords_pre, img_poly_pre, dcm_img_pre, angle)
    dcm_img_post = plot(img_post, coords_post, img_poly_post, dcm_img_post, 0)
    dcm = concatenate_images(dcm_img_pre, dcm_img_post)
    dcm.save(show_calculation_step_by_step_folder + os.sep + "ShowAngle.png")


def show_length_measurements(
    config,
    dicom_img,
    coords,
    line_params,
    point_params,
    angle,
    crop_img=False,
    center=None,
):
    cf_1 = {
        "overlay_dicom": False,
        "overlay_rois": True,
        "overlay_rois_alpha": 0.5,
        "overlay_EI": False,
        "overlay_lines": True,
        "crop_img": crop_img,
    }

    img_1 = plot_img(
        config,
        cf_1,
        dicom_img,
        coords,
        line_params,
        point_params,
        angle,
        center=center,
        crop_range=0.15,
    )
    img_1.save(show_calculation_step_by_step_folder + os.sep + "Length.png")


def show_EIs_measurements(
    config,
    dicom_img,
    coords,
    line_params,
    point_params,
    angle,
    crop_img=False,
    center=None,
):
    cf_1 = {
        "overlay_dicom": False,
        "overlay_rois": True,
        "overlay_rois_alpha": 0.5,
        "overlay_EI": True,
        "overlay_lines": False,
        "crop_img": crop_img,
    }

    img_1 = plot_img(
        config,
        cf_1,
        dicom_img,
        coords,
        line_params,
        point_params,
        angle,
        center=center,
        crop_range=0.15,
    )
    img_1.save(show_calculation_step_by_step_folder + os.sep + "EIs.png")


def show_center_points(dcm_img, points):
    rv_endo = points[0]
    lv_epi = points[3]
    lv_endo = points[4]
    septum_center = points[5]

    draw, img_poly, dcm_img = get_img(dcm_img)
    color = ["red", "blue", "green", "black"]
    font = ImageFont.truetype("arial.ttf", 30)
    names = ["P3", "P4", "P5", "P6"]
    for i, p in enumerate([rv_endo, lv_epi, lv_endo, septum_center]):
        circle_size = 5
        draw.ellipse(
            (
                p[0] - circle_size,
                p[1] - circle_size,
                p[0] + circle_size,
                p[1] + circle_size,
            ),
            outline=color[i],
            fill=color[i],
            width=4,
        )
        if i != 2:
            draw.text((p[0], p[1] + 30), names[i], font=font, fill=color[i])
        else:
            draw.text((p[0] + 20, p[1] - 30), names[i], font=font, fill=color[i])

    dcm_img.paste(img_poly, mask=img_poly)

    x, y = septum_center[0], septum_center[1]
    h, w = dcm_img.size
    h = round(0.12 * h)
    w = round(0.12 * w)
    dcm_img = dcm_img.crop([x - w, y - h, x + w, y + h])
    dcm_img.save(show_calculation_step_by_step_folder + os.sep + "CenterPoints.png")
