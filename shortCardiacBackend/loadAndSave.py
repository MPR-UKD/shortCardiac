import csv
import glob
import os
import pandas as pd
import numpy as np

import moviepy.video.io.ImageSequenceClip
import pydicom
from PIL import Image
from natsort.natsort import natsorted

from shortCardiacBackend.supportFunction import is_file_a_dicom, adjust_gamma


def load_DICOMs(folder: str, fast_mode: bool = False) -> [list, list]:
    """
    Read out all Dicom files in the directory and all subdirectories.

         Parameters:
                folder (str): Folder
                fast_mode (bool): Specifies that all Dicom images have the suffix '*.dcm'; this allows much faster browsing of the directory tree.

        Returns:
            dcms = list of all found Dicom files
            uis = list with all imported dicom uis
    """
    print("Start loading of DICOM images")
    # load list with all dicom files
    dcms, uis = [], []
    for (dirpath, dirnames, filenames) in os.walk(folder):
        for filename in filenames:
            if fast_mode and os.path.splitext(filename)[-1] == "dcm":
                continue
            dcm_file = os.path.join(dirpath, filename)
            # Checks if the file is a DICOM file; if so, the file and ui will saved
            if is_file_a_dicom(dcm_file):
                uis.append(pydicom.dcmread(dcm_file).SOPInstanceUID)
                dcms.append(dcm_file)
    return dcms, uis


def load_dcm_as_PIL(dcm_file: str, resize_factor: int = 1):
    """
    Returns resized dicom image as Pillow RGB Image

            Parameters:
                    dcm_file (str): Path to dicom image
                    resize_factor (int): rescaling factor for DICOM images

            Returns:
                    dcm_img (Pillow Image): dcm_image as RGB image
    """

    dicom = pydicom.dcmread(dcm_file).pixel_array.astype("float32")

    # rescale DICOM image to RGB scaling
    dicom_rgb = dicom / dicom.max() * 255

    # resizing and converting to RGB
    return (
        Image.fromarray(dicom_rgb)
        .resize((dicom.shape[1] * resize_factor, dicom.shape[0] * resize_factor))
        .convert("RGB")
    )


def save(results, dicom_folder):
    customized_saving_technical_note(results, dicom_folder)


def customized_saving_technical_note(results, dicom_folder):
    """
    Customized function to save results, other formats could add
    """
    # D0 = septum length
    def calc_D0(params, params_name):
        index_0 = params_name.index(
            "septum_center_to_right_ventricle_endo_ventral 0° [mm]"
        )
        index_180 = params_name.index(
            "septum_center_to_right_ventricle_endo_ventral 180° [mm]"
        )
        D0 = params[index_0] + params[index_180]
        D0_name = "D0"
        return D0, D0_name

    def params_to_string(params):
        """
        convert params to string

        :param params: tuple of list with params

        :return: string with params
        """
        params = [str(p).replace(",", "\\").replace(".", ",") + ";" for p in params]
        return "".join(s for s in params)

    first_img = True
    for i, result in enumerate(results):
        file, params, params_name = result
        if len(params) == 0:
            continue
        D0, D0_name = calc_D0(params, params_name)
        if first_img:
            string_results = (
                "Mode;file;"
                + "".join([name + ";" for name in params_name + [D0_name]])
                + "\n"
            )
            first_img = False
        df = pydicom.dcmread(file)
        Mode = file.replace(dicom_folder, "").split("\\")[1]
        string_results += (
            Mode
            + ";"
            + file.replace(dicom_folder, "")
            + ";"
            + params_to_string(params + [D0])
            + "\n"
        )
    if first_img:
        print("Error")
        return None
    with open(dicom_folder + r"\results_de.csv", "w+") as csv_file:
        csv_file.writelines(string_results)
    with open(dicom_folder + r"\results_eng.csv", "w+") as csv_file:
        csv_file.writelines(string_results.replace(",", "."))


def generate_mp4(folder: str, fps: int = 3) -> None:
    """
    creates an mp4-video with the saved images

    :param folder: path to saved images
    :param fps: Video fps
    """
    images = natsorted(glob.glob(folder + os.sep + "*.png"))
    clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(images, fps=fps)
    clip.write_videofile(folder + os.sep + "result_video.mp4")


def load_result_csv(file: str) -> pd.DataFrame:
    """
    load result.csv file as pandas dataframe - worked with ',' and '.' separators

    :param file: path to csv-file
    :return: pandas dataframe
    """
    with open(file) as file_obj:
        reader_obj = csv.reader(file_obj, delimiter=";")
        header = None
        lines = []

        def transform_value(value):
            try:
                value = float(value.replace(",", "."))
            except ValueError:
                pass
            return value

        for i, row in enumerate(reader_obj):
            if i == 0:
                header = row
                continue

            lines.append([transform_value(_.replace(",", ".")) for _ in row])
    if header is None:
        return None
    return pd.DataFrame(np.array(lines, dtype=object), columns=header)
