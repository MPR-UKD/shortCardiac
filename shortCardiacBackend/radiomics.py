import SimpleITK as sitk
import numpy as np
import pydicom
import radiomics
import six
from PIL import Image, ImageDraw
from radiomics import firstorder, glcm, glrlm, glszm, shape2D
from radiomics import setVerbosity
from shortCardiacBackend.supportFunction import flatted_list


def calc_mask_of_polygon_for_radiomics(
    dcm_img: str, coords: dict, name: str, resize_polygon_factor: int
) -> np.ndarray:
    """

    :param dcm_img: path to DICOM image
    :param coords: dict with all segmentation coordinates
    :param name: name of segmentation - key for coords dict
    :param resize_polygon_factor: factor between segmentation coords and original DICOM image

    :return: bool mask with ones and zeros
    """
    dcm_shape = pydicom.dcmread(dcm_img).pixel_array.shape
    img = Image.new("L", (dcm_shape[1], dcm_shape[0]), 0)
    img_draw = ImageDraw.Draw(img)
    c = tuple(
        [
            (c1 / resize_polygon_factor, c2 / resize_polygon_factor)
            for c1, c2 in list(coords.get(name))
        ]
    )
    img_draw.polygon(c, outline=1, fill=1)
    return np.array(img)


def calc_radiomics(
    dcm_file: str, mask: np.ndarray, name: str, normalize: bool = False, cf: dict = None
):
    """
    function for calculation of radiomcs features - wrapper fuction for pyradiomics

    more information: https://pyradiomics.readthedocs.io/en/latest/
    """

    if cf is None:
        cf = {
            "shape_feature": True,
            "firstorder_feature": True,
            "glcm_feature": True,
            "glrlm_feature": True,
            "glszm_feature": True,
        }
    setVerbosity(60)
    dcm_sitk = sitk.GetImageFromArray(pydicom.dcmread(dcm_file).pixel_array)
    if normalize:
        dcm_sitk = radiomics.imageoperations.normalizeImage(dcm_sitk)
    mask_sitk = sitk.GetImageFromArray(mask)

    def extract_results(res, feauture_class=None):
        feature, feature_names = [], []
        for key, val in six.iteritems(res):
            if "Version" in key or "Settings" in key or "Configuration" in key:
                continue
            feature.append(val)
            _ = "" if feauture_class is None else feauture_class + "_"
            feature_names.append(
                _
                + name
                + "_"
                + key.replace("original_", "").replace("diagnostics_", "")
            )

        return feature, feature_names

    feature_list = []
    feature_names_list = []

    if cf["shape_feature"]:
        shape_extractor = shape2D.RadiomicsShape2D(dcm_sitk, mask_sitk)
        shape_results = shape_extractor.execute()
        feature, feature_names = extract_results(shape_results, "shape")
        feature_list.append(feature)
        feature_names_list.append(feature_names)

    if cf["firstorder_feature"]:
        firstorder_extractor = firstorder.RadiomicsFirstOrder(dcm_sitk, mask_sitk)
        firstorder_results = firstorder_extractor.execute()
        feature, feature_names = extract_results(firstorder_results, "firstorder")
        feature_list.append(feature)
        feature_names_list.append(feature_names)

    if cf["glcm_feature"]:
        gclm_extractor = glcm.RadiomicsGLCM(dcm_sitk, mask_sitk)
        glcm_results = gclm_extractor.execute()
        feature, feature_names = extract_results(glcm_results, "glcm")
        feature_list.append(feature)
        feature_names_list.append(feature_names)

    if cf["glrlm_feature"]:
        glrlm_extractor = glrlm.RadiomicsGLRLM(dcm_sitk, mask_sitk)
        glrlm_results = glrlm_extractor.execute()
        feature, feature_names = extract_results(glrlm_results, "glrlm")
        feature_list.append(feature)
        feature_names_list.append(feature_names)

    if cf["glszm_feature"]:
        glszm_extractor = glszm.RadiomicsGLSZM(dcm_sitk, mask_sitk)
        glszm_results = glszm_extractor.execute()
        feature, feature_names = extract_results(glszm_results, "glszm")
        feature_list.append(feature)
        feature_names_list.append(feature_names)

    return flatted_list(feature_list), flatted_list(feature_names_list)
