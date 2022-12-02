import cv2
import nibabel as nib
import numpy as np
import pydicom
from scipy.ndimage.morphology import binary_fill_holes

from shortCardiacBackend.CoordCVI42 import *
from shortCardiacBackend.transformContours import mask_to_polygon


class CoordReader:
    def __init__(self, config):
        self.config = config

    def load_coordinates(self, file):
        """
        Import of the coordinates segmented in Circle. If the file is a pickle file ('*.pkl'), the coordinates are imported directly.
        Alternatively, the data is first prepared and then imported.
        """
        if ".pkl" not in file:
            print(
                "Invalid file format! Please use a preparation function to translate the coordinates to the correct format."
            )
            return None
        with open(file, "rb") as f:
            return pickle.load(f)

    def preparation_cvi42(self, cvi42_file, save_file_name=None):
        """
        Reading out the coordinates and assigning them to the dicom files

                Parameters:
                        cvi42_file (str): circle-xml file with coordinates
                        uis (list): list with included dicom uis
                        coord_attributes = ....

                Returns:
                        coordinates (dict: dict with dicom ui as key
        """
        save_file_name = (
            save_file_name if save_file_name is not None else cvi42_file + ".pkl"
        )
        parseFile(cvi42_file, save_file_name)

    def preparation_nii(self, nii_file, dcm_sorted, save_file_name=None):
        ids = [
            self.config.rv_name_or_nr,
            self.config.lv_epi_name_or_nr,
            self.config.lv_endo_name_or_nr,
        ]
        mask = self.__load_nifti(nii_file)
        coords = self.__get_polygon_of_mask(mask, dcm_sorted, ids)

        with open(save_file_name, "wb") as f:
            pickle.dump(coords, f)

    def __load_nifti(self, nii_file: str) -> np.ndarray:
        nimg = nib.load(nii_file)
        return nimg.get_fdata()[:, :, ::-1].transpose(1, 0, 2)

    def __get_polygon_of_mask(self, mask, dcm_sorted, ids, up_scaling=4):
        coords = {}

        for i, dcm_file in enumerate(dcm_sorted):
            ui = pydicom.dcmread(dcm_file).SOPInstanceUID
            coords[ui] = {}
            slice_mask = mask[:, :, i].copy().astype("int16")
            r, g, b = slice_mask.copy(), slice_mask.copy(), slice_mask.copy()

            r[r != int(ids[0])] = 0
            r[r == int(ids[0])] = 255
            g[g != int(ids[1])] = 0
            g[g == int(ids[1])] = 255
            b[b != int(ids[2])] = 0
            b[b == int(ids[2])] = 255
            temp_rgb = cv2.merge([r, g, b])
            temp_rgb = cv2.blur(temp_rgb, (2, 2))
            temp_rgb = cv2.resize(
                temp_rgb,
                dsize=(temp_rgb.shape[0] * up_scaling, temp_rgb.shape[0] * up_scaling),
                interpolation=cv2.INTER_AREA,
            )
            temp_rgb = cv2.blur(temp_rgb, (5, 5))
            slice_mask = np.zeros((temp_rgb.shape[0], temp_rgb.shape[1]))
            r, g, b = cv2.split(temp_rgb)
            for x in range(slice_mask.shape[0]):
                for y in range(slice_mask.shape[1]):
                    if all([r[x, y] < 100, g[x, y] < 100, b[x, y] < 100]):
                        continue
                    slice_mask[x, y] = (
                        np.argmax(np.array([r[x, y], g[x, y], b[x, y]])) + 1
                    )
            for ii, id in enumerate(ids):
                id = int(id)

                temp = slice_mask.copy()
                temp[temp != id] = 0
                temp[temp == id] = 1
                temp = binary_fill_holes(temp).astype(int)

                coords[ui][str(id)] = mask_to_polygon(temp) / up_scaling

        return coords
