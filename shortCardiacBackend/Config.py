import json

# Default RunConfiguration


class RunConfiguration(object):
    def __init__(self):
        # Using the DebugMode, only one image is loaded; however, several outputs are generated,
        # which visualize the functioning of the script and the current calculations step by step.
        self.DEBUG = False

        self.coord_mode = 'nii'

        ##############################################
        # Activate and deactivate calculation
        # --------------------------------------------
        # More specific settings can change on the
        # end of the config file
        ##############################################
        self.calc_features = True
        # self.calc_right_ventricle_endocard = True
        # self.calc_left_ventricular_epicard = True
        # self.calc_left_ventricular_endocard = True

        # Used number of processes
        self.worker = 0

        ###############################################
        # Image Mode Selection
        ##############################################
        self.img_transparent = True
        self.save_pngs = True
        self.crop_img = True  # Boolean specifying whether the image should be cropped to the heart center
        self.crop_x = 0.25  # percent as float in range 0 - 1
        self.crop_y = 0.25  # percent as float in range 0 - 1
        # first image
        self.first_img_overlay_dicom = True
        self.first_img_overlay_rois = False
        self.first_img_overlay_rois_alpha = 0.4  # hint: float in range 0 - 1
        self.first_img_overlay_EI = True
        self.first_img_overlay_lines = False
        # second image
        self.second_img = True
        self.second_img_overlay_dicom = False
        self.second_img_overlay_rois = True
        self.second_img_overlay_rois_alpha = 0.2  # hint: float in range 0 - 1
        self.second_img_overlay_EI = False
        self.second_img_overlay_lines = True


        # ############################################## Resolution Settings
        # ############################################# Factor by which the read coordinates are scaled up for a more
        # precise calculation (integer between 1 and infinity). Note: The higher the resolution the longer the
        # calculation and the more RAM is needed. The script was optimized using factor 8
        self.resize_polygon_factor = 8

        ###############################################
        # Coordinates Correction Setting
        ###############################################
        # Indicates whether the heart angle is to be corrected in a standardized manner.
        self.angle_correction = True
        # Specifies whether the heart angle should be corrected in a standardized way.
        self.smooth_resizing = True

        ################################################
        # Calculations for the right ventricle endocard
        ###############################################
        # Indication of the name used by Circle for the contour of the right ventricle.
        self.rv_name_or_nr = "sarvendocardialContour"
        # Settings for measuring the ventral contour of the right ventricle
        self.rv_endo_ventral_angle_min = 0
        self.rv_endo_ventral_angle_max = 180
        self.rv_endo_ventral_angle_step_size = 15
        # Settings for measuring the dorsal contour of the right ventricle
        self.rv_endo_dorsal_angle_min = 0
        self.rv_endo_dorsal_angle_max = 180
        self.rv_endo_dorsal_angle_step_size = 15

        ################################################
        # Calculations for the left ventricular epicard
        ###############################################
        self.lv_epi_name_or_nr = "saepicardialContour"
        self.lv_epi_angle_min = 0
        self.lv_epi_angle_max = 360
        self.lv_epi_angle_step_size = 15

        ################################################
        # Calculations for the left ventricular endocard
        # ################################################
        self.lv_endo_name_or_nr = "saendocardialContour"
        self.lv_endo_angle_min = 0
        self.lv_endo_angle_max = 360
        self.lv_endo_angle_step_size = 15

    def generate_dict(self):
        return {key: value for key, value in self.__dict__.items() if not key.startswith('__') and not callable(key)}

    def save_to_json(self, save_file):
        information = self.generate_dict()
        js = json.dumps(information)

        with open(save_file if '.json' in save_file else save_file + '.json', 'w+') as f:
            f.write(js)

    def load_from_json(self, json_file):
        pass
