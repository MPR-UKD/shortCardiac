import numpy as np
from PIL import Image, ImageDraw, ImageFont

from shortCardiacBackend.transformContours import calc_center_of_polygon, rotate_points


def show_segmentation(config, dicom_img, coords):
    """

    :param dicom_img: dicom as PIL image
    :param coords: list of np-array with coords
    :param line_params: list with np-array of two points that define a line [[(px_1,py_1),(px_2,py_2)],...]
    :param point_params: list with points [np.array([px_1,py_1]), np.array([px_2,py_2]), ....]
    :param resize: Resize factor to save the image with a higher resolution.
    :return: resized dicom as PIL image
    """
    # plot_all_contours(coords, dicom_img, angle)

    coords = [
        coords.get(config.lv_epi_name_or_nr),
        coords.get(config.lv_endo_name_or_nr),
        coords.get(config.rv_name_or_nr),
    ]

    dicom_img = dicom_img.convert("RGBA")
    if config.img_transparent:
        back = Image.new("RGBA", dicom_img.size)
    else:
        back = Image.new("RGBA", dicom_img.size, color="white")

    img_poly = Image.new("RGBA", dicom_img.size)
    img = ImageDraw.Draw(img_poly, "RGBA")
    a = 150
    colors = [(0, 0, 100, a), (0, 100, 0, a), (100, 0, 0, a), (100, 100, 100, a)]

    for i, c in enumerate(coords):
        if c is None:
            continue

        c = tuple([(c1, c2) for c1, c2 in c])
        try:
            img.polygon(c, fill=colors[i], outline=colors[i])
        except:
            pass
    dicom_cut_out = dicom_img.load()
    for x in range(img_poly.size[0]):
        for y in range(img_poly.size[1]):
            dicom_cut_out[x, y] = (
                dicom_cut_out[x, y][0],
                dicom_cut_out[x, y][1],
                dicom_cut_out[x, y][2],
                0,
            )

    # dicom_img.paste(img_poly, mask=img_poly)
    back.paste(img_poly, mask=img_poly)
    if config.second_img:
        dicom_img = concatenate_images(dicom_img, back)
    return dicom_img


def rotate_img(img, angle):
    return img.rotate(angle)


def concatenate_images(img1, img2):
    """
    Merges two images side by side

            Parameters:
                    img1 (Pillow Image): Image 1 (left)
                    img2 (Pillow Image): Image 2 (right)

            Returns:
                    img_conc (Pillow Image): Image 1 and image 2 next to each other
    """
    # creating a new image
    img_conc = Image.new(
        "RGBA",
        (
            img1.size[0] + img2.size[0],
            img1.size[1] if img1.size[1] > img2.size[1] else img2.size[1],
        ),
    )

    # pasting the first image (image_name, (position))
    img_conc.paste(img1, (0, 0))

    # pasting the second image (image_name, (position))
    img_conc.paste(img2, (img1.size[0], 0))
    return img_conc


def visualization(
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
        "overlay_dicom": config.first_img_overlay_dicom,
        "overlay_rois": config.first_img_overlay_rois,
        "overlay_rois_alpha": config.first_img_overlay_rois_alpha,
        "overlay_EI": config.first_img_overlay_EI,
        "overlay_lines": config.first_img_overlay_lines,
        "img_transparent": config.img_transparent,
        "crop_img": "show_box",  # crop_img,
        "angle_correction": False,
    }

    cf_2 = {
        "overlay_dicom": config.second_img_overlay_dicom,
        "overlay_rois": config.second_img_overlay_rois,
        "overlay_rois_alpha": config.second_img_overlay_rois_alpha,
        "overlay_EI": config.second_img_overlay_EI,
        "overlay_lines": config.second_img_overlay_lines,
        "img_transparent": False,
        "crop_img": crop_img,
        "angle_correction": True,
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
    if config.second_img:
        img_2 = plot_img(
            config,
            cf_2,
            dicom_img,
            coords,
            line_params,
            point_params,
            angle,
            center=center,
            crop_range=0.15,
            scaling=3,
        )

        if img_2.size != img_1.size:
            img_2 = img_2.resize(img_1.size)
        img_1 = concatenate_images(img_1, img_2)
        # img_1 = show_legend(img_1)
        b = 2
    return img_1


def show_legend(img):
    draw = ImageDraw.Draw(img, "RGBA")
    x = img.size[0] / 2 + 20
    y = img.size[1] - img.size[1] / 3
    delta_y = 80
    colors = ["red"] + ["orange"] + ["blue"] + ["green"] + ["black"]
    name = [
        "Septum Center to ventral right ventricle endocard contour",
        "Septum Center to dorsal right ventricle endocard contour",
        "Center to left ventricle epicard contour",
        "Center to left ventricle endocard contour",
        "angle-dependent length measurements",
    ]
    font = ImageFont.truetype("arial.ttf", 60)
    for i in range(5):
        if i < 4:
            p = tuple([(x, y - delta_y * i), (x + 20, y - delta_y * i)])
            draw.line(p, fill=colors[i], width=6)
        if i == 4:
            font = ImageFont.truetype("arial.ttf", 80)
        draw.text((x + 40, y - delta_y * i - 20), name[i], font=font, fill=colors[i])
    return img


def plot_img(
    config,
    img_cf,
    dicom_img,
    coords,
    line_params,
    point_params,
    angle,
    center=None,
    crop_range=None,
    scaling=None,
):
    """

    :param dicom_img: dicom as PIL image
    :param coords: list of np-array with coords
    :param line_params: list with np-array of two points that define a line [[(px_1,py_1),(px_2,py_2)],...]
    :param point_params: list with points [np.array([px_1,py_1]), np.array([px_2,py_2]), ....]
    :param resize: Resize factor to save the image with a higher resolution.
    :return: resized dicom as PIL image
    """
    if scaling is None or img_cf["crop_img"] == False:
        scaling = 1
    if center is not None:
        center = center * scaling
    pre_size = dicom_img.size
    dicom_img = dicom_img.resize((scaling * pre_size[0], scaling * pre_size[1]))
    center_img = (dicom_img.size[0] / 2, dicom_img.size[1] / 2)
    if not img_cf["overlay_dicom"]:
        if img_cf["img_transparent"]:
            dicom_img = Image.new("RGBA", dicom_img.size)
        else:
            dicom_img = Image.new("RGBA", dicom_img.size, color="white")
    if img_cf["angle_correction"]:
        dicom_img = dicom_img.convert("RGBA").rotate(-angle)
    else:
        dicom_img = dicom_img.convert("RGBA")
    img_poly = Image.new("RGBA", dicom_img.size)
    img = ImageDraw.Draw(img_poly, "RGBA")
    coords = [
        coords.get(config.lv_epi_name_or_nr) * scaling,
        coords.get(config.lv_endo_name_or_nr) * scaling,
        coords.get(config.rv_name_or_nr) * scaling,
    ]
    # Wenn in der Config Datei angegeben, werden die eingezeichneten ROIs überlagert
    if img_cf["overlay_rois"]:
        a = int(255 * img_cf["overlay_rois_alpha"])

        colors = [(0, 0, 100, a), (0, 100, 0, a), (100, 0, 0, a), (100, 100, 100, a)]

        for i, c in enumerate(coords):
            if c is None:
                continue
            c = tuple([(c1, c2) for c1, c2 in c])
            if not img_cf["angle_correction"]:
                c = rotate_points(c, center_img, -angle)
                c = [tuple(_) for _ in c]
            try:
                color_a = colors[i]
                color_a = (color_a[0], color_a[1], color_a[2], 250)
                img.polygon(c, fill=colors[i], outline=color_a)
            except:
                pass
    # TODO: Remove after Paper exception only necessary for 3D plot
    """
    if True:
        img_cut_off = Image.new('RGBA', dicom_img.size)
        draw = ImageDraw.Draw(img_cut_off, 'RGBA')
        for i, c in enumerate(coords):
            if c is None:
                continue
            c = tuple([(c1, c2) for c1, c2 in c])
            try:
                draw.polygon(c, fill='red', outline='red')
            except:
                pass
        cut_out = img_cut_off.load()
        dicom_cut_out = dicom_img.load()
        for x in range(img_poly.size[0]):
            for y in range(img_poly.size[1]):
                if cut_out[x,y][0] > 0 or cut_out[x,y][1] > 0 or cut_out[x,y][2] > 0:
                    continue
                dicom_cut_out[x,y] = (dicom_cut_out[x,y][0], dicom_cut_out[x,y][1], dicom_cut_out[x,y][2], 50)
    """
    colors = (
        ["red"]
        + ["orange"]
        + ["blue"]
        + ["green"]
        + ["red"]
        + ["blue"]
        + ["green"]
        + ["orange"]
        + ["black"] * 100
    )
    width = [
        2 * scaling,
        2 * scaling,
        2 * scaling,
        2 * scaling,
        6 * scaling,
        6 * scaling,
        6 * scaling,
        6 * scaling,
    ]
    for i, lines in enumerate(line_params):
        if lines == [[]] or lines is None:
            continue
        lines = [(p1 * scaling, p2 * scaling) for p1, p2 in lines]
        if not img_cf["angle_correction"]:
            lines = [tuple(rotate_points(line, center_img, -angle)) for line in lines]
        if i < 4 and not img_cf["overlay_lines"]:
            continue
        if i >= 4 and not img_cf["overlay_EI"]:
            continue
        for p in lines:
            if p is None:
                continue
            p = tuple([(p1, p2) for p1, p2 in p])
            img.line(p, fill=colors[i], width=width[i])
            if p[0][0] == p[1][0] and i >= 4:
                min_, max_ = p[0][0] - 10, p[0][0] + 10
                img.line(
                    ((min_, p[0][1]), (max_, p[0][1])), fill=colors[i], width=width[i]
                )
                img.line(
                    ((min_, p[1][1]), (max_, p[1][1])), fill=colors[i], width=width[i]
                )
            if p[0][1] == p[1][1] and i >= 4:
                min_, max_ = p[0][1] - 10, p[0][1] + 10
                img.line(
                    (
                        (p[0][0], min_),
                        (
                            p[0][0],
                            max_,
                        ),
                    ),
                    fill=colors[i],
                    width=width[i],
                )
                img.line(
                    (
                        (p[1][0], min_),
                        (
                            p[1][0],
                            max_,
                        ),
                    ),
                    fill=colors[i],
                    width=width[i],
                )
    if img_cf["crop_img"] == "show_box":
        x = center[0]
        y = center[1]
        h, w = dicom_img.size
        p1 = (
            (x - round(0.25 * h), y - round(0.25 * h))
            if crop_range is None
            else (x - round(crop_range * h), y - round(crop_range * h))
        )
        p2 = (
            (x - round(0.25 * h), y + round(0.25 * h))
            if crop_range is None
            else (x - round(crop_range * h), y + round(crop_range * h))
        )
        p3 = (
            (x + round(0.25 * h), y + round(0.25 * h))
            if crop_range is None
            else (x + round(crop_range * h), y + round(crop_range * h))
        )
        p4 = (
            (x + round(0.25 * h), y - round(0.25 * h))
            if crop_range is None
            else (x + round(crop_range * h), y - round(crop_range * h))
        )
        points = [p1, p2, p3, p4, p1]
        if not img_cf["angle_correction"]:
            points = rotate_points([p1, p2, p3, p4, p1], center_img, -angle)
        img.polygon([tuple(p) for p in points], outline="red", width=6)

    dicom_img.paste(img_poly, mask=img_poly)

    if type(img_cf["crop_img"]) == bool:
        if img_cf["crop_img"]:
            x = center[0]
            y = center[1]
            h, w = dicom_img.size
            h = round(0.25 * h) if crop_range is None else round(crop_range * h)
            w = round(0.25 * w) if crop_range is None else round(crop_range * w)
            dicom_img = dicom_img.crop([x - w, y - h, x + w, y + h])

    return dicom_img.convert("RGBA")
