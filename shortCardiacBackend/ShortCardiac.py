from abc import ABC

import matplotlib.pyplot as plt

from shortCardiacBackend.loadAndSave import load_dcm_as_PIL
from shortCardiacBackend.radiomics import calc_mask_of_polygon, calc_radiomics
from shortCardiacBackend.ShowCalculationsStepByStep import *
from shortCardiacBackend.SIConvertion import convert_params
from shortCardiacBackend.supportFunction import *
from shortCardiacBackend.transformContours import *
from shortCardiacBackend.transformPointsAndVectors import *
from shortCardiacBackend.visualisation import *


def display(image):
    plt.imshow(image)
    plt.show()


def check_coords(coords, config):
    if config.rv_name_or_nr not in coords.keys():
        return False
    if config.lv_endo_name_or_nr not in coords.keys():
        return False
    if config.lv_epi_name_or_nr not in coords.keys():
        return False
    try:
        calc_center_of_polygon(coords[config.rv_name_or_nr])
        calc_center_of_polygon(coords[config.lv_endo_name_or_nr])
        calc_center_of_polygon(coords[config.lv_epi_name_or_nr])
    except ZeroDivisionError:
        return False
    return True


class ShortCardiac(ABC):
    def __init__(self, config, dcm_file, coords):
        self.config = config
        self.dcm_file = dcm_file

        self.calculable = check_coords(coords, config)
        # show_segmentation(config, load_dcm_as_PIL(dcm_file, 1), coords)

        # Read in the dcm_image as a PILLOW image for the visualization of the calculations.
        self.dcm_img = load_dcm_as_PIL(dcm_file, config.resize_polygon_factor)
        coords_resizing(coords, config.resize_polygon_factor, config.smooth_resizing)
        self.showCalculationStepByStep = False

        if self.calculable:

            find_ref_points(coords, config)
            if coords["sacardialRefPoint"] is None:
                self.calculable = False

        if not self.calculable:
            self.dcm_img = show_segmentation(
                config, load_dcm_as_PIL(dcm_file, config.resize_polygon_factor), coords
            )
            if self.config.save_pngs:
                self.dcm_img.save(
                    self.dcm_file.replace(".dcm", ".png"),
                    transparent=self.config.img_transparent,
                )

        if self.calculable:
            if self.showCalculationStepByStep:
                show_Ref_points_and_septum_axis(self.dcm_img, coords, self.dcm_file)
            if self.showCalculationStepByStep:
                c_ = deepcopy(coords)
            correct_segmentations(coords, config)
            if self.showCalculationStepByStep:
                show_coord_correction(self.dcm_img, coords, c_, config)

            # Resizing the circle coordinates by the factor {resize_polygon_factor} allows a more stable calculation.
            # In addition, the missing points are added and the ROIs spline interpolated (smoothed).
            # For more information see function: smooth_coord_resizing and the documentation scipy.interpolate.splprep
            # (https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.splprep.html).
            # show_segmentation(config, load_dcm_as_PIL(dcm_file, 1), coords)

            # Division of the coordinates of the right ventricle into a ventral and dorsal contour.
            # The calculation uses the SAX Reference points if available:
            # --> S0 = superior SAX Reference point [sacardialRefPoint]
            # --> S1 = inferior SAX Reference point [sacardialInferiorRefPoint]
            # if these are not present they are automatically calculated based on the contours of the right ventricle and the
            # .... calculated

            # Detection of reference points: sacardialRefPoint and sacardialInferiorRefPoint if they are not present in the dataset.

            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! STILL NEEDS TO BE IMPLEMENTED !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

            # Calculation of septum alignment and correction for standardized measurement
            septum_angle = calc_cardiac_angle(coords)
            # if abs(septum_angle) > 7:
            #    self.showCalculationStepByStep = True
            # else:
            #    self.showCalculationStepByStep = False
            center_img = (self.dcm_img.size[0] / 2, self.dcm_img.size[1] / 2)
            if self.config.DEBUG:
                print(
                    f"ORGINAL DICOM IMAGE (left) AND DICOM IMAGE (right) AFTER THE HEART AXIS HAS BEEN CORRECTED BY {septum_angle}°."
                )
                img_conc = concatenate_images(
                    self.dcm_img, rotate_img(self.dcm_img, -septum_angle)
                )
                display(img_conc)
                print(" \n \n")
            if self.showCalculationStepByStep:
                coords_pre = deepcopy(coords)
            if config.angle_correction:
                for key in coords.keys():
                    coords[key] = np.array(
                        rotate_points(coords[key], center_img, septum_angle)
                    )
            if self.showCalculationStepByStep:
                show_angle(
                    self.dcm_img,
                    coords_pre,
                    rotate_img(self.dcm_img, -septum_angle),
                    coords,
                    center_img,
                    septum_angle,
                )
            self.septum_angle = septum_angle
            self.coords = coords

        self.septum_angle_name = "Septum_angle [°]"

        #    self.__init_parameters()

        # def __init_important_parameters(self):
        # quantitative_septum_evaluation
        self.septum_axis = [None]
        self.septum_axis_name = ["SeptumRefPoint", "SeptumInferiorRefPoint"]
        self.septum_center = None
        self.septum_center_name = "Center point between RefPoints"

        # quantitative_right_ventricle_evaluation
        self.Center_rv_endo = None
        self.Center_rv_endo_name = "Center_rv_endo"
        self.Area_rv_endo = None
        self.Area_rv_endo_name = "Area_rv_endo [cm^2]"
        self.Area_between_rv_endo_and_septum_axis = None
        self.Area_between_rv_endo_and_septum_axis_name = (
            "Area_between_rv_endo_and_septum_axis [cm^2]"
        )
        self.distance_rv_endo_ventral_to_septum_center = None
        self.distance_rv_endo_ventral_to_septum_center_name = [
            f"septum_center_to_right_ventricle_endo_ventral {i}° [mm]"
            for i in range(
                self.config.rv_endo_ventral_angle_min,
                self.config.rv_endo_ventral_angle_max + 1,
                self.config.rv_endo_ventral_angle_step_size,
            )
        ]
        self.distance_rv_endo_dorsal_to_septum_center = None
        self.distance_rv_endo_dorsal_to_septum_center_names = [
            f"septum_center_to_rv_endo_dorsal {i}° [mm]"
            for i in range(
                self.config.rv_endo_dorsal_angle_min,
                self.config.rv_endo_dorsal_angle_max + 1,
                self.config.rv_endo_dorsal_angle_step_size,
            )
        ]
        self.EI_line_rv_endo_0 = None
        self.EI_line_rv_endo_0_name = "EI_line_rv_endo_0 [mm]"
        self.EI_line_rv_endo_90 = None
        self.EI_line_rv_endo_90_name = "EI_line_rv_endo_90 [mm]"
        self.Septum_axis_to_rv_endo = None
        self.Septum_axis_to_rv_endo_name = "Septum_axis_to_rv_endo [mm]"
        self.Line_Intersection_EI_rv_endo = None
        self.Line_Intersection_EI_rv_endo_name = "Line_Intersection_EI_rv_endo"
        self.scope_rv_endo = None
        self.scope_rv_endo_name = "scope_rv_endo [mm]"

        # quantitative_saepicardial_contour_evaluation
        self.Center_lv_epi = None
        self.Center_lv_epi_name = "Center_lv_epi"
        self.Area_lv_epi = None
        self.Area_lv_epi_name = "Area_lv_epi [mm^2]"
        self.distance_lv_epi = None
        self.distance_lv_epi_name = [
            f"Distance_lv_epi {i}° [mm]"
            for i in range(
                self.config.lv_epi_angle_min,
                self.config.lv_epi_angle_max,
                self.config.lv_epi_angle_step_size,
            )
        ]
        self.EI_line_lv_epi_0 = None
        self.EI_line_lv_epi_0_name = "EI_line_lv_epi_0 [mm]"
        self.EI_line_lv_epi_90 = None
        self.EI_line_lv_epi_90_name = "EI_line_lv_epi_90 [mm]"
        self.Line_intersection_EI_lv_epi = None
        self.Line_Intersection_EI_lv_epi_name = "Line_Intersection_EI_lv_epi"
        self.scope_lv_epi = None
        self.scope_lv_epi_name = "scope_lv_epi [mm]"

        # quantitative_saendocardial_contour_evaluation
        self.Center_lv_endo = None
        self.Center_lv_endo_name = "Center_lv_endo"
        self.Area_lv_endo = None
        self.Area_lv_endo_name = "Area_lv_endo [mm^2]"
        self.EI_line_lv_endo_0 = None
        self.EI_line_lv_endo_0_name = "EI_line_lv_endo_0 [mm]"
        self.EI_line_lv_endo_90 = None
        self.EI_line_lv_endo_90_name = "EI_line_lv_endo_90 [mm]"
        self.Line_Intersection_EI_lv_endo = None
        self.Line_Intersection_EI_lv_endo_name = "Line_Intersection_EI_lv_endo"
        self.distance_lv_endo = None
        self.distance_lv_endo_name = [
            f"Distance_lv_endo {i}° [mm]"
            for i in range(
                self.config.lv_endo_angle_min,
                self.config.lv_endo_angle_max,
                self.config.lv_endo_angle_step_size,
            )
        ]
        self.scope_lv_endo = None
        self.scope_lv_endo_name = "scope_lv_endo [mm]"

        self.merged_params = None
        self.merged_param_names = None

    def run(self):
        if not self.calculable:
            self.merge_results()
            return self.dcm_file, [], self.merged_param_names
        try:
            # if True:
            self.feature_extraction()
            self.quantitative_septum_evaluation()
            self.quantitative_right_ventricle_evaluation()
            self.quantitative_saendocardial_contour_evaluation()
            self.quantitative_saepicardial_contour_evaluation()
            self.merge_results()
        # else:
        except Exception as e:
            self.merge_results()
            return self.dcm_file, [], self.merged_param_names
        return self.get_results()

    def generate_mask(self):
        right_ventricel_mask = calc_mask_of_polygon(
            self.dcm_file,
            self.coords,
            self.config.rv_name_or_nr,
            self.config.resize_polygon_factor,
        )
        saendocardialContour_mask = calc_mask_of_polygon(
            self.dcm_file,
            self.coords,
            self.config.lv_endo_name_or_nr,
            self.config.resize_polygon_factor,
        )
        saepicardialContour_mask = (
            calc_mask_of_polygon(
                self.dcm_file,
                self.coords,
                self.config.lv_epi_name_or_nr,
                self.config.resize_polygon_factor,
            )
            - saendocardialContour_mask
        )
        return right_ventricel_mask, saendocardialContour_mask, saepicardialContour_mask

    def feature_extraction(self):
        (
            right_ventricel_mask,
            saendocardialContour_mask,
            saepicardialContour_mask,
        ) = self.generate_mask()
        right_ventricel_feature = calc_radiomics(
            self.dcm_file,
            right_ventricel_mask,
            name=self.config.rv_name_or_nr,
            normalize=True,
        )
        saendocardialContour_feature = calc_radiomics(
            self.dcm_file,
            saendocardialContour_mask,
            name=self.config.lv_endo_name_or_nr,
            normalize=True,
        )
        saepicardialContour_feature = calc_radiomics(
            self.dcm_file,
            saepicardialContour_mask,
            name=self.config.lv_epi_name_or_nr,
            normalize=True,
        )
        self.radiomc_feature = {
            "right_ventricel": right_ventricel_feature,
            "saendocardialContour": saendocardialContour_feature,
            "saepicardialContour_feature": saepicardialContour_feature,
        }

    def get_results(self):
        if self.merged_params is None:
            print(
                "No calculation performed so far please use one of the following calculations first:"
                " [quantitative_septum_evaluation, quantitative_right_ventricle_evaluation, "
                "quantitative_saepicardial_contour_evaluation, quantitative_saendocardial_contour_evaluation]"
            )
            return None
        else:
            return self.dcm_file, self.merged_params, self.merged_param_names

    def quantitative_septum_evaluation(self):
        """---------------------------------------------------------------------------------------------------------"""
        """ Calculation of septum alignment and septum center (midpoint between the two reference points S0 & S1) """
        """ ---------------------------------------------------------------------------------------------------------"""

        # The septum alignment is determined by the two reference points "sacardialRefPoint" and "sacardialInferiorRefPoint."
        # The points are determined automatically by Circle; should the points not exist in the loaded workspace,
        # then, they were filled in the previous step, "Detection of reference points."
        self.septum_axis = [
            self.coords["sacardialRefPoint"][0],
            self.coords["sacardialInferiorRefPoint"][0],
        ]
        # Determination of the midpoint between the two reference points
        self.septum_center = calc_center_of_2_points(
            self.septum_axis[0], self.septum_axis[1]
        )

        return (self.septum_axis, self.septum_axis_name), (
            self.septum_center,
            self.septum_center_name,
        )

    def quantitative_right_ventricle_evaluation(self):
        """---------------------------------------------------------------------------------------------------------"""
        """ Calculations for the Right Ventricle """
        """ ---------------------------------------------------------------------------------------------------------"""

        # Calculation of the center of gravity \ center point for the "sarvendocardialContour" contour
        self.Center_rv_endo = calc_center_of_polygon(
            self.coords[self.config.rv_name_or_nr]
        )
        # Calculation of the area for the contour "sarvendocardialContour" - Note: Unit here still Pixel^2 Conversion to cm^2 only in function "convert_params
        self.Area_rv_endo = calc_area(self.coords[self.config.rv_name_or_nr])

        # Calculation of the area spanned by the dorsal contour of the right atrium - Note Unit here still Pixel^2 Conversion to cm^2 only in function "convert_params".
        self.Area_between_rv_endo_and_septum_axis = calc_area(
            self.coords["sarvendocardialContourDorsalClosed"]
        )

        # Calculation of Distance_Feauture for the ventral contour of the right ventricle.

        if self.septum_center is None:
            _ = self.quantitative_septum_evaluation()
        self.distance_rv_endo_ventral_to_septum_center = calc_outline(
            self.septum_center,
            self.coords["sarvendocardialContourVentral"],
            [
                i
                for i in range(
                    self.config.rv_endo_ventral_angle_min,
                    self.config.rv_endo_ventral_angle_max + 1,
                    self.config.rv_endo_ventral_angle_step_size,
                )
            ],
        )

        # Calculation of the Distance_Feauture for the dorsal contour of the right ventricle.
        self.distance_rv_endo_dorsal_to_septum_center = calc_outline(
            self.septum_center,
            self.coords["sarvendocardialContourDorsal"],
            [
                i
                for i in range(
                    self.config.rv_endo_dorsal_angle_min,
                    self.config.rv_endo_dorsal_angle_max + 1,
                    self.config.rv_endo_dorsal_angle_step_size,
                )
            ],
        )

        # Calculation of the longest diameters of the sarvendocardialContour at an angle of 0 and 90 degrees to the
        # cardiac axis for the calculation of the EI.
        self.EI_line_rv_endo_0 = calc_line_for_EI(
            self.coords[self.config.rv_name_or_nr], 0
        )

        self.EI_line_rv_endo_90 = calc_line_for_EI(
            self.coords[self.config.rv_name_or_nr], 90
        )

        # Calculation of the longest stretch antiparallel to the cardiac axis to describe the curvature of the right ventricle.
        try:
            self.Septum_axis_to_rv_endo = calc_line_for_EI(
                self.coords["sarvendocardialContourDorsalClosed"], 90
            )
        except ZeroDivisionError:
            self.calculable = False
            raise ZeroDivisionError

        # Calculation of the intersection of L1 & L2
        self.Line_Intersection_EI_rv_endo = line_intersection(
            self.EI_line_rv_endo_0, self.EI_line_rv_endo_90
        )

        # Calculation of the scope for sarvendocardialContour
        self.scope_rv_endo = calc_polygon_length(self.coords[self.config.rv_name_or_nr])

        return {
            "Center_rv_endo": self.Center_rv_endo,
            "Center_rv_endo_name": self.Center_rv_endo_name,
            "Area_rv_endo": self.Area_rv_endo,
            "Area_rv_endo_name": self.Area_rv_endo_name,
            "Area_between_rv_endo_and_septum_axis": self.Area_between_rv_endo_and_septum_axis,
            "Area_between_rv_endo_and_septum_axis_name": self.Area_between_rv_endo_and_septum_axis_name,
            "distance_rv_endo_ventral_to_septum_center": self.distance_rv_endo_ventral_to_septum_center,
            "distance_rv_endo_ventral_to_septum_center_name": self.distance_rv_endo_ventral_to_septum_center_name,
            "distance_rv_endo_dorsal_to_septum_center": self.distance_rv_endo_dorsal_to_septum_center,
            "distance_rv_endo_dorsal_to_septum_center_names": self.distance_rv_endo_dorsal_to_septum_center_names,
            "EI_line_rv_endo_0": self.EI_line_rv_endo_0,
            "EI_line_rv_endo_0_name": self.EI_line_rv_endo_0_name,
            "EI_line_rv_endo_90": self.EI_line_rv_endo_90,
            "EI_line_rv_endo_90_name": self.EI_line_rv_endo_90_name,
            "Septum_axis_to_rv_endo": self.Septum_axis_to_rv_endo,
            "Septum_axis_to_rv_endo_name": self.Septum_axis_to_rv_endo_name,
            "Line_Intersection_EI_rv_endo": self.Line_Intersection_EI_rv_endo,
            "Line_Intersection_EI_rv_endo_name": self.Line_Intersection_EI_rv_endo_name,
            "scope_rv_endo": self.scope_rv_endo,
            "scope_rv_endo_name": self.scope_rv_endo_name,
        }

    def quantitative_saepicardial_contour_evaluation(self):
        """---------------------------------------------------------------------------------------------------------"""
        """ Calculations for saepicardialContour """
        """ ---------------------------------------------------------------------------------------------------------"""

        # Calculation of the center of gravity \ center point for the "saepicardialContour" contour
        self.Center_lv_epi = calc_center_of_polygon(
            self.coords[self.config.lv_epi_name_or_nr]
        )

        # Calculation of the area for the contour "saepicardialContour" - Note: Unit here still Pixel^2 Conversion to cm^2 only in function "convert_params"
        self.Area_lv_epi = calc_area(self.coords[self.config.lv_epi_name_or_nr])

        # Calculation of the Distance_Feauture for the contour of the saepicardialContour
        self.distance_lv_epi = calc_outline(
            self.Center_lv_epi,
            self.coords[self.config.lv_epi_name_or_nr],
            [
                i
                for i in range(
                    self.config.lv_epi_angle_min,
                    self.config.lv_epi_angle_max,
                    self.config.lv_epi_angle_step_size,
                )
            ],
        )

        # Calculation of the longest diameters of the saepicardialContour at an angle of 0 and 90 degrees to the cardiac axis for the calculation of the EI.
        self.EI_line_lv_epi_0 = calc_line_for_EI(
            self.coords[self.config.lv_epi_name_or_nr], 0
        )
        self.EI_line_lv_epi_90 = calc_line_for_EI(
            self.coords[self.config.lv_epi_name_or_nr], 90
        )

        # Calculation of the intersection of L3 & L4
        self.Line_intersection_EI_lv_epi = line_intersection(
            self.EI_line_lv_epi_0, self.EI_line_lv_epi_90
        )

        # Calculation of the scope for sarvendocardialContour
        self.scope_lv_epi = calc_polygon_length(
            self.coords[self.config.lv_epi_name_or_nr]
        )

        return {
            "Center_lv_epi": self.Center_lv_epi,
            "Center_lv_epi_name": self.Center_lv_epi_name,
            "Area_lv_epi": self.Area_lv_epi,
            "Area_lv_epi_name": self.Area_lv_epi_name,
            "distance_lv_epi": self.distance_lv_epi,
            "distance_lv_epi_name": self.distance_lv_epi_name,
            "EI_line_lv_epi_0": self.EI_line_lv_epi_0,
            "EI_line_lv_epi_0_name": self.EI_line_lv_epi_0_name,
            "EI_line_lv_epi_90": self.EI_line_lv_epi_90,
            "EI_line_lv_epi_90_name": self.EI_line_lv_epi_90_name,
            "Line_intersection_EI_lv_epi": self.Line_intersection_EI_lv_epi,
            "Line_Intersection_EI_lv_epi_name": self.Line_Intersection_EI_lv_epi_name,
            "scope_lv_epi": self.scope_lv_epi,
            "scope_lv_epi_name": self.scope_lv_epi_name,
        }

    def quantitative_saendocardial_contour_evaluation(self):
        """---------------------------------------------------------------------------------------------------------"""
        """ Calculations for saendocardialContour """
        """ ---------------------------------------------------------------------------------------------------------"""

        # Calculation of the center of gravity \ center point for the "saendocardialContour" contour
        self.Center_lv_endo = calc_center_of_polygon(
            self.coords[self.config.lv_endo_name_or_nr]
        )
        # Calculation of the area for the contour "saendocardialContour"
        # Note: Unit here still Pixel^2 Conversion to cm^2 only in function "convert_params
        self.Area_lv_endo = calc_area(self.coords[self.config.lv_endo_name_or_nr])
        # Calculation of the longest diameters of the saendocardialContour at an angle of 0 and 90 degrees to the cardiac axis for the analysis of the EI.
        self.EI_line_lv_endo_0 = calc_line_for_EI(
            self.coords[self.config.lv_endo_name_or_nr], 0
        )
        self.EI_line_lv_endo_90 = calc_line_for_EI(
            self.coords[self.config.lv_endo_name_or_nr], 90
        )
        # Calculation of the intersection of L5 & L6
        self.Line_Intersection_EI_lv_endo = line_intersection(
            self.EI_line_lv_endo_0, self.EI_line_lv_endo_90
        )

        # Calculation of the Distance_Feauture for the contour of the saendocardialContour
        self.distance_lv_endo = calc_outline(
            self.Center_lv_endo,
            self.coords[self.config.lv_endo_name_or_nr],
            [
                i
                for i in range(
                    self.config.lv_endo_angle_min,
                    self.config.lv_endo_angle_max,
                    self.config.lv_endo_angle_step_size,
                )
            ],
        )

        # Calculation of the scope for saendocardialContour
        self.scope_lv_endo = calc_polygon_length(
            self.coords[self.config.lv_endo_name_or_nr]
        )

        return {
            "Center_lv_endo": self.Center_lv_endo,
            "Center_lv_endo_name": self.Center_lv_endo_name,
            "Area_lv_endo": self.Area_lv_endo,
            "Area_lv_endo_name": self.Area_lv_endo_name,
            "EI_line_lv_endo_0": self.EI_line_lv_endo_0,
            "EI_line_lv_endo_0_name": self.EI_line_lv_endo_0_name,
            "EI_line_lv_endo_90": self.EI_line_lv_endo_90,
            "EI_line_lv_endo_90_name": self.EI_line_lv_endo_90_name,
            "Line_Intersection_EI_lv_endo": self.Line_Intersection_EI_lv_endo,
            "Line_Intersection_EI_lv_endo_name": self.Line_Intersection_EI_lv_endo_name,
            "distance_lv_endo": self.distance_lv_endo,
            "distance_lv_endo_name": self.distance_lv_endo_name,
            "scope_lv_endo": self.scope_lv_endo,
            "scope_lv_endo_name": self.scope_lv_endo_name,
        }

    def merge_results(self):
        """------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
        """ Merge the parameters into the line_params, poit_params and area_params """
        """ ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
        line_params_names = (
            [self.distance_rv_endo_ventral_to_septum_center_name]
            + [self.distance_rv_endo_dorsal_to_septum_center_names]
            + [self.distance_lv_epi_name]
            + [self.distance_lv_endo_name]
            + [[self.EI_line_rv_endo_0_name] + [self.EI_line_rv_endo_90_name]]
            + [[self.EI_line_lv_epi_0_name] + [self.EI_line_lv_epi_90_name]]
            + [[self.EI_line_lv_endo_0_name] + [self.EI_line_lv_endo_90_name]]
            + [[self.Septum_axis_to_rv_endo_name]]
        )
        line_params = (
            [self.distance_rv_endo_ventral_to_septum_center]
            + [self.distance_rv_endo_dorsal_to_septum_center]
            + [self.distance_lv_epi]
            + [self.distance_lv_endo]
            + [[self.EI_line_rv_endo_0] + [self.EI_line_rv_endo_90]]
            + [[self.EI_line_lv_epi_0] + [self.EI_line_lv_epi_90]]
            + [[self.EI_line_lv_endo_0] + [self.EI_line_lv_endo_90]]
            + [[self.Septum_axis_to_rv_endo]]
        )

        point_params = (
            [self.Center_rv_endo]
            + list(self.septum_axis)
            + [self.Center_lv_epi]
            + [self.Center_lv_endo]
            + [self.septum_center]
            + [
                self.Line_Intersection_EI_rv_endo,
                self.Line_intersection_EI_lv_epi,
                self.Line_Intersection_EI_lv_endo,
            ]
        )
        point_params_names = (
            [self.Center_rv_endo_name]
            + self.septum_axis_name
            + [self.Center_lv_epi_name]
            + [self.Center_lv_endo_name]
            + [self.septum_center_name]
            + [
                self.Line_Intersection_EI_rv_endo_name,
                self.Line_Intersection_EI_lv_epi_name,
                self.Line_Intersection_EI_lv_endo_name,
            ]
        )
        scope_params = [self.scope_rv_endo, self.scope_lv_epi, self.scope_lv_endo]
        scope_params_name = [
            self.scope_rv_endo_name,
            self.scope_lv_epi_name,
            self.scope_lv_endo_name,
        ]

        area_params = [
            self.Area_rv_endo,
            self.Area_between_rv_endo_and_septum_axis,
            self.Area_lv_epi,
            self.Area_lv_endo,
        ]
        area_params_name = [
            self.Area_rv_endo_name,
            self.Area_between_rv_endo_and_septum_axis_name,
            self.Area_lv_epi_name,
            self.Area_lv_endo_name,
        ]

        """ ---------------------------------------------------------------------------------------------------------"""
        """ Visualization of the calculated parameters """
        """ ---------------------------------------------------------------------------------------------------------"""

        if self.showCalculationStepByStep:
            show_center_points(self.dcm_img.rotate(-self.septum_angle), point_params)
            show_length_measurements(
                self.config,
                self.dcm_img,
                self.coords,
                line_params,
                point_params,
                angle=self.septum_angle,
                crop_img=self.config.crop_img if not self.config.DEBUG else False,
                center=self.septum_center,
            )
            show_EIs_measurements(
                self.config,
                self.dcm_img,
                self.coords,
                line_params,
                point_params,
                angle=self.septum_angle,
                crop_img=self.config.crop_img if not self.config.DEBUG else False,
                center=self.septum_center,
            )

        if (self.config.save_pngs or self.config.DEBUG) and self.calculable:
            self.dcm_img = visualization(
                self.config,
                self.dcm_img,
                self.coords,
                line_params,
                point_params,
                angle=self.septum_angle,
                crop_img=self.config.crop_img if not self.config.DEBUG else False,
                center=self.septum_center,
            )
            if self.config.save_pngs:
                self.dcm_img.save(
                    self.dcm_file.replace(".dcm", ".png"),
                    transparent=self.config.img_transparent,
                )
            else:
                display(self.dcm_img)

        if self.calculable:
            """---------------------------------------------------------------------------------------------------------"""
            """ Conversion of the determined parameters into SI units """
            """ ---------------------------------------------------------------------------------------------------------"""
            pixel_spacing = get_pixel_spacing(self.dcm_file)
            line_params = flatted_list(line_params)

            params = convert_params(
                line_params,
                point_params,
                area_params,
                scope_params,
                self.config.resize_polygon_factor,
                pixel_spacing,
            )

            """ ---------------------------------------------------------------------------------------------------------"""
            """ Calculation of EIs """
            """ ---------------------------------------------------------------------------------------------------------"""

            EIs = [
                calc_EI(self.EI_line_rv_endo_0, self.EI_line_rv_endo_90),
                calc_EI(self.EI_line_lv_epi_0, self.EI_line_lv_epi_90),
                calc_EI(self.EI_line_lv_endo_0, self.EI_line_lv_endo_90),
            ]

        EIs_name = ["EI_rv_endo", "EI_lv_epi", "EI_lv_endo"]

        """ ---------------------------------------------------------------------------------------------------------"""
        """ Reading Dicom tags and writing Dicomtags. """
        """ ---------------------------------------------------------------------------------------------------------"""

        # params_dicom_tags, params_dicom_tags_name = read_dicom_tags(self.dcm_file)
        # add_dicom_tags() Muss noch implementiert werden

        self.dcm_file = self.dcm_file
        if self.calculable:
            self.merged_params = (
                [self.septum_angle]
                + flatted_list(params)
                + EIs
                + self.radiomc_feature["right_ventricel"][0]
                + self.radiomc_feature["saendocardialContour"][0]
                + self.radiomc_feature["saepicardialContour_feature"][0]
            )
        else:
            self.merged_params = None
        # + params_dicom_tags
        self.merged_param_names = (
            [self.septum_angle_name]
            + flatted_list(line_params_names)
            + point_params_names
            + area_params_name
            + scope_params_name
            + EIs_name
        )
        if self.config.calc_features and self.calculable:
            self.merged_param_names += (
                self.radiomc_feature["right_ventricel"][1]
                + self.radiomc_feature["saendocardialContour"][1]
                + self.radiomc_feature["saepicardialContour_feature"][1]
            )  # + params_dicom_tags_name


def read_dicom_tags(file):
    """
    Reading out parameters stored in DicomTags

    :param file: string with path to dicom image
    :return:
    """
    ds = pydicom.dcmread(file)
    Trigger_time = ds[0x0018, 0x1060].value
    InstanceNumber = ds[0x0019, 0x0001].value
    # custom, custom_name = [], []
    # for custom_key in config.custom_keys:
    #    Atemfluss = ds[0x0019, 0x0002].value
    #    Atemvolumen = ds[0x0019, 0x0003].value
    # return [Trigger_time, InstanceNumber, Atemfluss, Atemvolumen], \
    #       ["Trigger_time", "InstanceNumber", "Atemfluss", "Atemvolumen"]
    return [Trigger_time, InstanceNumber], ["Trigger_time", "InstanceNumber"]


def calc_EI(d1, d2):
    d1 = length(get_vector(np.array(d1[0]), np.array(d1[1])))
    d2 = length(get_vector(np.array(d2[0]), np.array(d2[1])))
    return d1 / d2


def calc_cardiac_angle(coords):
    """
    Determination of the heart angle using the two reference points, sacardialRefPoint, and sacardialInferiorRefPoint.

            Parameters:
                    coords (dict): .....

            Returns:
                    angle (float): heart angle
    """
    sacardialRefPoint, sacardialInferiorRefPoint = (
        coords.get("sacardialRefPoint")[0],
        coords.get("sacardialInferiorRefPoint")[0],
    )
    angle = calc_angle(
        get_vector(sacardialRefPoint, sacardialInferiorRefPoint), np.array([0, -1])
    )
    if sacardialRefPoint[0] > sacardialInferiorRefPoint[0]:
        return -angle
    return angle


def calc_outline(origin, roi, angles):
    D = find_distance_with_angles_and_fixed_point(roi, angles, origin)
    return tuple([(D[key][0], D[key][1]) for key in D.keys()])
