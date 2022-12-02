import pydicom


def adjust_gamma(image, gamma=1.0):
    """
    convert image to gamma adjusted image

    :param image: image as np.array
    :param gamma: float

    :return: image after gamma adjustment
    """
    for x in range(image.shape[0]):
        for y in range(image.shape[1]):
            image[x, y] = (image[x, y] / 255) ** (1 / gamma) * 255
    return image


def get_pixel_spacing(file: str):
    """
    Get pixel spacing of dicom file

    :param: file (str):  path to the file to identify

    :return: spacing (dict): x = x_spacing, y = y_spacing
    """
    x_space = float(pydicom.dcmread(file).PixelSpacing[0])
    y_space = float(pydicom.dcmread(file).PixelSpacing[1])
    return {"x": x_space, "y": y_space}


def flatted_list(lists):
    """
    flat a list of sublist to one large list

    :param lists: list with sublists
    :return: flatted list
    """
    flat_list = []
    for sublist in lists:
        flat_list += sublist
    return flat_list


def is_file_a_dicom(file):
    """
    check if a file is a DICOM file

    :param file: path to the file to identify
    :return: is_dicom - True if the file is DICOM, False otherwise
    """
    try:
        pydicom.dcmread(file)
    except pydicom.errors.InvalidDicomError:
        return False
    return True


def parse_to_arguments(config, coords, dicom_files, uis):
    """
    Arranges the imported coordinates and dicom_files into tuples for the later calculations.
    Note: In DEBUG mode, the number of returned arguments is reduced to 1.

            Parameters:
                    coords (dict): Dictionary with dicom_ui as key, where the extracted coordinates are stored
                    dicom_files (list): List of paths to the Dicom files
                    uis (list): List with all imported Dicom UIs

            Returns:
                    args (tuple): (path to dicom file (str), Coordinates (dict))
    """

    def clear_keys(keys, uis):
        out_keys = []
        for key in keys:
            if key in uis:
                out_keys.append(key)
        return out_keys

    args = [
        (config, dicom_files[uis.index(ui)], coords.get(ui))
        for ui in clear_keys(coords.keys(), uis)
    ]
    if config.DEBUG:
        print("WARNING: DEBUG_MODE ONLY REDUCED LIST OF ARGUMENTS FOR THE CALCULATIONS")
        args = args[:1]
    return args
