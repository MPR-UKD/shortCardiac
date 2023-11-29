import json
import multiprocessing
import os
import sys
from multiprocessing import freeze_support

import pydicom.encoders
import PyQt5.sip
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QFile, QRect, QSize, Qt, QTextStream, QThread, pyqtSignal
from PyQt5.QtWidgets import *

from main import *
from shortCardiacBackend.Config import RunConfiguration



class MySwitch(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setMinimumWidth(66)
        self.setMinimumHeight(22)

    def paintEvent(self, event):
        label = "ON" if self.isChecked() else "OFF"
        bg_color = Qt.green if self.isChecked() else Qt.red

        radius = 10
        width = 32
        center = self.rect().center()

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.translate(center)
        painter.setBrush(QtGui.QColor(0, 0, 0))

        pen = QtGui.QPen(Qt.black)
        pen.setWidth(2)
        painter.setPen(pen)

        painter.drawRoundedRect(
            QRect(-width, -radius, 2 * width, 2 * radius), radius, radius
        )
        painter.setBrush(QtGui.QBrush(bg_color))
        sw_rect = QRect(-radius, -radius, width + radius, 2 * radius)
        if not self.isChecked():
            sw_rect.moveLeft(-width)
        painter.drawRoundedRect(sw_rect, radius, radius)
        painter.drawText(sw_rect, Qt.AlignCenter, label)


def set_angle_dependent_measurements(
    main_window, configs_layout, column_, row_, column_size, row_size
):
    config = QTabWidget()
    config_layout = QGridLayout()
    #
    caption_text = QLabel("Angle dependent measurements")
    myFont = QtGui.QFont()
    myFont.setPointSize(10)
    myFont.setBold(True)
    caption_text.setFont(myFont)
    row = 0
    config_layout.addWidget(caption_text, row, 0, 1, 2)
    caption_text = QLabel("right ventricle")
    myFont = QtGui.QFont()
    myFont.setBold(True)
    caption_text.setFont(myFont)
    row += 1
    config_layout.addWidget(caption_text, row, 0, 1, 2)
    row += 1
    rv_name_or_nr_text = QLabel("name or number: ")
    rv_name_or_nr = QLineEdit("sarvendocardialContour")
    main_window.rv_name_or_nr = rv_name_or_nr
    config_layout.addWidget(rv_name_or_nr_text, row, 1)
    config_layout.addWidget(rv_name_or_nr, row, 2, 1, 2)
    row += 1
    ventral_text = QLabel("ventral: ")
    ventral_min = QLabel("min [°]")
    ventral_max = QLabel("max [°]")
    ventral_step_size = QLabel("step size [°]")
    config_layout.addWidget(ventral_text, row, 0)
    config_layout.addWidget(ventral_min, row, 1)
    config_layout.addWidget(ventral_max, row, 2)
    config_layout.addWidget(ventral_step_size, row, 3)

    row += 1
    ventral_min = QSpinBox()
    ventral_max = QSpinBox()
    ventral_step_size = QSpinBox()
    main_window.ventral_min = ventral_min
    main_window.ventral_max = ventral_max
    main_window.ventral_step_size = ventral_step_size
    config_layout.addWidget(ventral_min, row, 1)
    config_layout.addWidget(ventral_max, row, 2)
    config_layout.addWidget(ventral_step_size, row, 3)

    row += 1
    dorsal_text = QLabel("dorsal: ")
    dorsal_min = QLabel("min [°]")
    dorsal_max = QLabel("max [°]")
    dorsal_step_size = QLabel("step size [°]")
    config_layout.addWidget(dorsal_text, row, 0)
    config_layout.addWidget(dorsal_min, row, 1)
    config_layout.addWidget(dorsal_max, row, 2)
    config_layout.addWidget(dorsal_step_size, row, 3)

    row += 1
    dorsal_min = QSpinBox()
    dorsal_max = QSpinBox()
    dorsal_step_size = QSpinBox()
    main_window.dorsal_min = dorsal_min
    main_window.dorsal_max = dorsal_max
    main_window.dorsal_step_size = dorsal_step_size

    config_layout.addWidget(dorsal_min, row, 1)
    config_layout.addWidget(dorsal_max, row, 2)
    config_layout.addWidget(dorsal_step_size, row, 3)

    row += 1
    caption_text = QLabel("left ventricle")
    caption_text.setFont(myFont)
    config_layout.addWidget(caption_text, row, 0, 1, 3)

    row += 1

    endocard_text = QLabel("endocard: ")
    endocard_min = QLabel("min [°]")
    endocard_max = QLabel("max [°]")
    endocard_step_size = QLabel("step size [°]")
    config_layout.addWidget(endocard_text, row, 0)
    config_layout.addWidget(endocard_min, row, 1)
    config_layout.addWidget(endocard_max, row, 2)
    config_layout.addWidget(endocard_step_size, row, 3)

    row += 1
    endocard_min = QSpinBox()
    endocard_max = QSpinBox()
    endocard_step_size = QSpinBox()
    main_window.endocard_min = endocard_min
    main_window.endocard_max = endocard_max
    main_window.endocard_step_size = endocard_step_size
    config_layout.addWidget(endocard_min, row, 1)
    config_layout.addWidget(endocard_max, row, 2)
    config_layout.addWidget(endocard_step_size, row, 3)

    row += 1
    lv_endo_name_or_nr_text = QLabel("name or number: ")
    lv_endo_name_or_nr = QLineEdit("saendocardialContour")
    main_window.lv_endo_name_or_nr = lv_endo_name_or_nr
    config_layout.addWidget(lv_endo_name_or_nr_text, row, 1)
    config_layout.addWidget(lv_endo_name_or_nr, row, 2, 1, 2)

    row += 1
    epicard_text = QLabel("epicard: ")
    epicard_min = QLabel("min [°]")
    epicard_max = QLabel("max [°]")
    epicard_step_size = QLabel("step size [°]")

    config_layout.addWidget(epicard_text, row, 0)
    config_layout.addWidget(epicard_min, row, 1)
    config_layout.addWidget(epicard_max, row, 2)
    config_layout.addWidget(epicard_step_size, row, 3)

    row += 1
    epicard_min = QSpinBox()
    epicard_max = QSpinBox()
    epicard_step_size = QSpinBox()
    main_window.epicard_min = epicard_min
    main_window.epicard_max = epicard_max
    main_window.epicard_step_size = epicard_step_size
    config_layout.addWidget(epicard_min, row, 1)
    config_layout.addWidget(epicard_max, row, 2)
    config_layout.addWidget(epicard_step_size, row, 3)

    row += 1
    lv_epi_name_or_nr_text = QLabel("name or number: ")
    lv_epi_name_or_nr = QLineEdit("saepicardialContour")
    main_window.lv_epi_name_or_nr = lv_epi_name_or_nr
    config_layout.addWidget(lv_epi_name_or_nr_text, row, 1)
    config_layout.addWidget(lv_epi_name_or_nr, row, 2, 1, 2)

    row += 1
    verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
    config_layout.addItem(verticalSpacer)
    config.setLayout(config_layout)
    configs_layout.addWidget(config, column_, row_, column_size, row_size)


def set_visualisation(mainWindow, configs_layout, column_, row_, column_size, row_size):
    config = QTabWidget()
    config_layout = QGridLayout()
    caption_text = QLabel("Visualization")
    myFont = QtGui.QFont()
    myFont.setPointSize(10)
    myFont.setBold(True)
    caption_text.setFont(myFont)
    row = 0
    config_layout.addWidget(caption_text, row, 0, 1, 2)
    row += 1
    save_png = QLabel("Save Images")
    config_layout.addWidget(save_png, row, 0)
    save_png = MySwitch()
    mainWindow.save_png = save_png
    config_layout.addWidget(save_png, row, 1)
    row += 1
    crop_image = QLabel("Crop Image")
    config_layout.addWidget(crop_image, row, 0)
    crop_image = MySwitch()
    mainWindow.crop_image = crop_image
    config_layout.addWidget(crop_image, row, 1)
    row += 1
    crop_size = QLabel("Crop Size [%]")
    config_layout.addWidget(crop_size, row, 0)
    crop_size = QSpinBox()
    mainWindow.crop_size = crop_size
    config_layout.addWidget(crop_size, row, 1)
    row += 1
    caption_text = QLabel("First Image")
    myFont = QtGui.QFont()
    myFont.setBold(True)
    caption_text.setFont(myFont)
    config_layout.addWidget(caption_text, row, 0, 1, 2)
    row += 1
    fisrt_img_dicom_transparence = QLabel("DICOM transparency [%]")
    config_layout.addWidget(fisrt_img_dicom_transparence, row, 0)
    fisrt_img_dicom_transparence = QSpinBox()
    mainWindow.first_img_dicom_transparence = fisrt_img_dicom_transparence
    config_layout.addWidget(fisrt_img_dicom_transparence, row, 1)
    row += 1
    first_img_overlay_dicom = QLabel("Overlay DICOM")
    config_layout.addWidget(first_img_overlay_dicom, row, 0)
    first_img_overlay_dicom = MySwitch()
    mainWindow.first_img_overlay_dicom = first_img_overlay_dicom
    config_layout.addWidget(first_img_overlay_dicom, row, 1)
    row += 1
    first_img_overlay_rois = QLabel("Overlay ROIs")
    config_layout.addWidget(first_img_overlay_rois, row, 0)
    first_img_overlay_rois = MySwitch()
    mainWindow.first_img_overlay_rois = first_img_overlay_rois
    config_layout.addWidget(first_img_overlay_rois, row, 1)
    row += 1
    first_img_overlay_rois_alpha = QLabel("Overlay ROIs alpha [%]")
    config_layout.addWidget(first_img_overlay_rois_alpha, row, 0)
    first_img_overlay_rois_alpha = QSpinBox()
    mainWindow.first_img_overlay_rois_alpha = first_img_overlay_rois_alpha
    config_layout.addWidget(first_img_overlay_rois_alpha, row, 1)
    row += 1
    first_img_overlay_EI = QLabel("Overlay EIs")
    config_layout.addWidget(first_img_overlay_EI, row, 0)
    first_img_overlay_EI = MySwitch()
    mainWindow.first_img_overlay_EI = first_img_overlay_EI
    config_layout.addWidget(first_img_overlay_EI, row, 1)
    row += 1
    first_img_overlay_lines = QLabel("Show angle dependent measurements")
    config_layout.addWidget(first_img_overlay_lines, row, 0)
    first_img_overlay_lines = MySwitch()
    mainWindow.first_img_overlay_lines = first_img_overlay_lines
    config_layout.addWidget(first_img_overlay_lines, row, 1)
    row += 1
    caption_text = QLabel("Second Image")
    myFont = QtGui.QFont()
    myFont.setBold(True)
    caption_text.setFont(myFont)
    config_layout.addWidget(caption_text, row, 0, 1, 2)
    row += 1
    second_img = QLabel("Plot second image")
    config_layout.addWidget(second_img, row, 0)
    second_img = MySwitch()
    mainWindow.second_img = second_img
    config_layout.addWidget(second_img, row, 1)
    row += 1
    second_img_dicom_transparence = QLabel("DICOM transparency [%]")
    config_layout.addWidget(second_img_dicom_transparence, row, 0)
    second_img_dicom_transparence = QSpinBox()
    mainWindow.second_img_dicom_transparence = second_img_dicom_transparence
    config_layout.addWidget(second_img_dicom_transparence, row, 1)
    row += 1
    second_img_overlay_dicom = QLabel("Overlay dicom")
    config_layout.addWidget(second_img_overlay_dicom, row, 0)
    second_img_overlay_dicom = MySwitch()
    mainWindow.second_img_overlay_dicom = second_img_overlay_dicom
    config_layout.addWidget(second_img_overlay_dicom, row, 1)
    row += 1
    second_img_overlay_rois = QLabel("Overlay ROIs")
    config_layout.addWidget(second_img_overlay_rois, row, 0)
    second_img_overlay_rois = MySwitch()
    mainWindow.second_img_overlay_rois = second_img_overlay_rois
    config_layout.addWidget(second_img_overlay_rois, row, 1)
    row += 1
    second_img_overlay_rois_alpha = QLabel("Overlay ROIs alpha [%]")
    config_layout.addWidget(second_img_overlay_rois_alpha, row, 0)
    second_img_overlay_rois_alpha = QSpinBox()
    mainWindow.second_img_overlay_rois_alpha = second_img_overlay_rois_alpha
    config_layout.addWidget(second_img_overlay_rois_alpha, row, 1)
    row += 1
    second_img_overlay_EI = QLabel("Overlay EIs")
    config_layout.addWidget(second_img_overlay_EI, row, 0)
    second_img_overlay_EI = MySwitch()
    mainWindow.second_img_overlay_EI = second_img_overlay_EI
    config_layout.addWidget(second_img_overlay_EI, row, 1)
    row += 1
    second_img_overlay_lines = QLabel("Show angle dependent measurements")
    config_layout.addWidget(second_img_overlay_lines, row, 0)
    second_img_overlay_lines = MySwitch()
    mainWindow.second_img_overlay_lines = second_img_overlay_lines
    config_layout.addWidget(second_img_overlay_lines, row, 1)
    row += 1
    verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
    config_layout.addItem(verticalSpacer)
    config.setLayout(config_layout)
    configs_layout.addWidget(config, column_, row_, column_size, row_size)


def set_calculation_features(
    mainWindow, configs_layout, column_, row_, column_size, row_size
):
    config = QTabWidget()
    config_layout = QGridLayout()
    caption_text = QLabel("Radiomics texture analyses")
    myFont = QtGui.QFont()
    myFont.setBold(True)
    myFont.setPointSize(10)
    caption_text.setFont(myFont)
    config_layout.addWidget(caption_text, 0, 0, 1, 2)

    shape_feature_text = QLabel("2D shape:")
    firstorder_feature_text = QLabel("Firstorder:")
    glcm_feature_text = QLabel("GLCM:")
    glrlm_feature_text = QLabel("GLRLM:")
    glszm_feature_text = QLabel("GLSZM:")
    config_layout.addWidget(shape_feature_text, 1, 0)
    config_layout.addWidget(firstorder_feature_text, 2, 0)
    config_layout.addWidget(glcm_feature_text, 3, 0)
    config_layout.addWidget(glrlm_feature_text, 4, 0)
    config_layout.addWidget(glszm_feature_text, 5, 0)

    shape_feature = MySwitch()
    firstorder_feature = MySwitch()
    glcm_feature = MySwitch()
    glrlm_feature = MySwitch()
    glszm_feature = MySwitch()

    mainWindow.shape_feature = shape_feature
    mainWindow.firstorder_feature = firstorder_feature
    mainWindow.glcm_feature = glcm_feature
    mainWindow.glrlm_feature = glrlm_feature
    mainWindow.glszm_feature = glszm_feature

    config_layout.addWidget(shape_feature, 1, 1)
    config_layout.addWidget(firstorder_feature, 2, 1)
    config_layout.addWidget(glcm_feature, 3, 1)
    config_layout.addWidget(glrlm_feature, 4, 1)
    config_layout.addWidget(glszm_feature, 5, 1)

    verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
    config_layout.addItem(verticalSpacer)
    config.setLayout(config_layout)
    config.setMaximumHeight(180)
    configs_layout.addWidget(config, column_, row_, column_size, row_size)


def set_settings(mainWindow, configs_layout):
    config = QTabWidget()
    # Anzahl an Workern für die Parallelisierung
    config_layout = QGridLayout()
    caption_text = QLabel("General Settings")
    myFont = QtGui.QFont()
    myFont.setPointSize(10)
    myFont.setBold(True)
    caption_text.setFont(myFont)
    config_layout.addWidget(caption_text, 0, 0)
    #
    worker_text = QLabel("Number of workers:")
    config_layout.addWidget(worker_text, 1, 0)
    worker_num = QSpinBox()
    mainWindow.worker_num = worker_num

    config_layout.addWidget(worker_num, 1, 1)
    #
    resolution_text = QLabel("rescaling factor:")
    config_layout.addWidget(resolution_text, 2, 0)
    rescaling_factor = QSpinBox()
    mainWindow.rescaling_factor = rescaling_factor
    config_layout.addWidget(rescaling_factor, 2, 1)
    #
    angle_correction_text = QLabel("angle correction:")
    config_layout.addWidget(angle_correction_text, 1, 2)
    angle_correction = MySwitch()
    mainWindow.angle_correction = angle_correction
    config_layout.addWidget(angle_correction, 1, 3)
    #
    smooth_resizing_text = QLabel("smooth resizing:")
    config_layout.addWidget(smooth_resizing_text, 2, 2)
    smooth_resizing = MySwitch()
    mainWindow.smooth_resizing = smooth_resizing
    config_layout.addWidget(smooth_resizing, 2, 3)
    verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
    config_layout.addItem(verticalSpacer)
    config.setLayout(config_layout)
    config.setMaximumHeight(100)
    configs_layout.addWidget(config)


def add_information(layout):
    info_layout = QGridLayout()
    version = QLabel("Version: 1.1.0 - ")
    myFont = QtGui.QFont()
    myFont.setPointSize(10)
    myFont.setBold(True)
    version.setFont(myFont)
    data = QLabel(" Nov 29, 2023")
    copyright_ = QLabel(
        "Copyright (C) 2023 - present; University Hospital Düsseldorf, Germany - "
        "License: GNU GENERAL PUBLICE LICENSE, Version 3, 29 June 2007"
    )
    citation = QLabel(
        "Citation: “shortCardiac” - an open-source framework for fast and standardized assessment of "
        "cardiac function; KL. Radke et al."
    )

    info_layout.addWidget(version, 0, 0)
    info_layout.addWidget(data, 0, 1)
    info_layout.addWidget(copyright_, 1, 0, 1, 60)
    info_layout.addWidget(citation, 2, 0, 1, 60)
    layout.addItem(info_layout)


def config_loading(mainWindow, config_layout):
    button_layout = QHBoxLayout()
    config_load = QPushButton("Load configuration file")
    config_load.clicked.connect(mainWindow.load_config)
    config_save = QPushButton("Save configuration file")
    config_save.clicked.connect(mainWindow.save_config)
    config_reset = QPushButton("Reset configuration settings")
    config_reset.clicked.connect(mainWindow.set_default)
    mainWindow.config_load = config_load
    mainWindow.config_save = config_save
    mainWindow.config_reset = config_reset
    button_layout.addWidget(config_load)
    button_layout.addWidget(config_save)
    button_layout.addWidget(config_reset)
    config_layout.addItem(button_layout)


def file_manager(mainWindow, file_manager_layout):
    ################## File Manager  ############################

    # Vorbereiten der Koordinaten
    coordinate_function_box = QComboBox()
    mainWindow.coordinate_function_box = coordinate_function_box
    coordinate_function_box.addItem("Cvi42")
    coordinate_function_box.addItem("nii.gz - file")
    coordinate_function_box.currentIndexChanged.connect(mainWindow.update_mode)
    mainWindow.coordinate_function_box = coordinate_function_box
    coordinate_function_box.addItem("-- chose loading function --")
    # coordinate_prepare_coords = QPushButton("Prepare coordinate file")

    # coordinate_prepare_coords.setStyleSheet("background-color : blue")
    file_manager_layout.addWidget(coordinate_function_box, 0, 0)
    # file_manager_layout.addWidget(coordinate_prepare_coords, 0, 1)
    # Einlesen der Koordinaten
    coordinate_load_button = QPushButton("Load coordinates")
    # coordinate_load_button.setStyleSheet("background-color : blue")
    coordinate_line_edit = QLineEdit()
    mainWindow.coordinate_line_edit = coordinate_line_edit
    # coordinate_line_edit.setStyleSheet("background-color : gray")
    file_manager_layout.addWidget(coordinate_load_button, 1, 0)
    file_manager_layout.addWidget(coordinate_line_edit, 1, 1)
    # Einlesen DICOM
    dicom_load_button = QPushButton("Load DICOM-Folder")
    # dicom_load_button.setStyleSheet("background-color : blue")
    dicom_line_edit = QLineEdit()
    mainWindow.dicom_line_edit = dicom_line_edit
    file_manager_layout.addWidget(dicom_load_button, 2, 0)
    file_manager_layout.addWidget(dicom_line_edit, 2, 1)
    run = QPushButton("Run")
    run.setMinimumHeight(80)
    myFont = QtGui.QFont()
    myFont.setPointSize(12)
    myFont.setBold(True)
    run.setFont(myFont)
    run.setStyleSheet("background-color : red")
    run.clicked.connect(mainWindow.run_shortCardiac)
    file_manager_layout.addWidget(run, 0, 2, 3, 1)

    coordinate_load_button.clicked.connect(
        mainWindow.coordinate_prepare_coords_function
    )
    dicom_load_button.clicked.connect(mainWindow.dicom_load_function)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.information = {}
        self.mode = "cvi42"
        self.setWindowTitle(
            "shortCardiac - an open-source framework for fast and standardized assessing cardiac functionality"
        )
        myFont = QtGui.QFont()
        myFont.setPointSize(8)
        self.setFont(myFont)
        layout = QVBoxLayout()

        file_manager_layout = QGridLayout()
        file_manager(self, file_manager_layout)
        ################## Config File  ############################
        config = QTabWidget()
        config_HBoxLayout = QVBoxLayout()
        config_GridLayout = QGridLayout()

        self.setMinimumSize(QSize(1200, 1000))
        config_loading(self, config_HBoxLayout)
        set_settings(self, config_HBoxLayout)
        set_angle_dependent_measurements(self, config_GridLayout, 0, 0, 2, 1)
        set_calculation_features(self, config_GridLayout, 2, 0, 1, 1)
        set_visualisation(self, config_GridLayout, 0, 1, 3, 1)

        config_HBoxLayout.addItem(config_GridLayout)
        add_information(config_HBoxLayout)
        widget = QWidget()
        layout.addLayout(file_manager_layout)
        config.setLayout(config_HBoxLayout)
        layout.addWidget(config)
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.set_ranges()
        self.set_default()
        self.setFont(QtGui.QFont("Times"))
        # self.coordinate_prepare_coords_function()

    def update_mode(self):
        if self.coordinate_function_box.currentIndex() == 1:
            self.mode = "nii"
        elif self.coordinate_function_box.currentIndex() == 0:
            self.mode = "cvi42"
        else:
            self.mode = "cvi42"
            self.coordinate_function_box.setCurrentIndex(0)
        self.set_names()

    def dicom_load_function(self):
        path = QtCore.QDir.currentPath()
        dialog = QFileDialog.getExistingDirectory(self, "Select dicom folder", path)
        self.dicom_line_edit.setText(dialog)

    def coordinate_prepare_coords_function(self):
        path = QtCore.QDir.currentPath()
        dialog = QFileDialog.getOpenFileName(self, "Select coordinate file", path, "*")
        self.coordinate_line_edit.setText(dialog[0])
        msg = None
        if ".nii" in dialog[0]:
            if self.coordinate_function_box.currentIndex() != 1:
                msg = QMessageBox()
                msg.setWindowTitle("User massage")
                msg.setText(
                    "Nifti file selected, but the current mode is cvi42! \n \n Mode changed to nii"
                )
            self.coordinate_function_box.setCurrentIndex(1)
        elif "cvi42wsx" in dialog[0]:
            if self.coordinate_function_box.currentIndex() != 0:
                msg = QMessageBox()
                msg.setWindowTitle("User massage")
                msg.setText(
                    "Cvi42 file selected, but the current mode is nii! \n \n Mode changed to cvi42"
                )
            self.coordinate_function_box.setCurrentIndex(0)
        elif ".pkl" in dialog[0]:
            pass
        else:
            msg = QMessageBox()
            msg.setWindowTitle("User massage")
            msg.setText(
                "Unknown file type selected, please select '.nii', '.nii.gz' or '.cvi42wsx'"
            )
            self.coordinate_line_edit.setText("")

        if msg is not None:
            msg.exec_()

    def run_shortCardiac(self):
        config = self.create_config()
        dicom_folder = self.dicom_line_edit.text()
        coord_file = self.coordinate_line_edit.text()
        if "" == dicom_folder or "" == coord_file:
            return None
        self.setEnabled(False)
        main(coord_file=coord_file, dcm_folder=dicom_folder, config=config)
        self.setEnabled(True)
        msg = QMessageBox()
        msg.setWindowTitle("User massage")
        msg.setText("Calculations successfully completed")
        msg.exec_()
        self.dicom_line_edit.setText("")
        self.coordinate_line_edit.setText("")

    def set_ranges(self):
        self.ventral_max.setMaximum(180)
        self.dorsal_max.setMaximum(180)
        self.epicard_max.setMaximum(360)
        self.endocard_max.setMaximum(360)
        self.worker_num.setMinimum(0)
        self.worker_num.setMaximum(24)
        self.first_img_overlay_rois_alpha.setMaximum(100)
        self.second_img_overlay_rois_alpha.setMaximum(100)
        self.rescaling_factor.setMinimum(1)
        self.rescaling_factor.setMaximum(24)

    def set_names(self):
        if self.mode == "cvi42":
            self.rv_name_or_nr.setText("sarvendocardialContour")
            self.lv_epi_name_or_nr.setText("saepicardialContour")
            self.lv_endo_name_or_nr.setText("saendocardialContour")
        elif self.mode == "nii":
            self.rv_name_or_nr.setText("1")
            self.lv_epi_name_or_nr.setText("2")
            self.lv_endo_name_or_nr.setText("3")
        else:
            raise UserWarning

    def set_default(self):
        self.set_names()
        self.ventral_max.setValue(self.ventral_max.maximum())
        self.ventral_step_size.setValue(15)
        self.dorsal_max.setValue(self.dorsal_max.maximum())
        self.dorsal_step_size.setValue(15)
        self.epicard_max.setValue(self.epicard_max.maximum())
        self.epicard_step_size.setValue(15)
        self.endocard_max.setValue(self.endocard_max.maximum())
        self.endocard_step_size.setValue(15)
        self.rescaling_factor.setValue(8)

        self.second_img.setChecked(True)
        self.save_png.setChecked(True)
        self.crop_image.setChecked(True)
        self.crop_size.setValue(20)

        self.worker_num.setValue(8)

        self.shape_feature.setChecked(True)
        self.firstorder_feature.setChecked(True)
        self.glcm_feature.setChecked(True)
        self.glrlm_feature.setChecked(True)
        self.glszm_feature.setChecked(True)
        self.angle_correction.setChecked(True)
        self.smooth_resizing.setChecked(True)

        self.first_img_dicom_transparence.setValue(25)

        self.first_img_overlay_dicom.setChecked(True)
        self.first_img_overlay_rois.setChecked(False)
        self.first_img_overlay_rois_alpha.setValue(40)
        self.first_img_overlay_EI.setChecked(True)
        self.first_img_overlay_lines.setChecked(False)
        self.second_img.setChecked(True)
        self.second_img_overlay_dicom.setChecked(False)
        self.second_img_overlay_rois.setChecked(True)
        self.second_img_overlay_rois_alpha.setValue(20)
        self.second_img_overlay_EI.setChecked(False)
        self.second_img_overlay_lines.setChecked(True)

    def save_config(self):
        config = {
            "rv_name_or_nr": self.rv_name_or_nr.text(),
            "lv_epi_name_or_nr": self.lv_epi_name_or_nr.text(),
            "lv_endo_name_or_nr": self.lv_endo_name_or_nr.text(),
            "ventral_max": self.ventral_max.value(),
            "ventral_step_size": self.ventral_step_size.value(),
            "dorsal_max": self.dorsal_max.value(),
            "dorsal_step_size": self.dorsal_step_size.value(),
            "epicard_max": self.epicard_max.value(),
            "epicard_step_size": self.epicard_step_size.value(),
            "endocard_max": self.endocard_max.value(),
            "endocard_step_size": self.endocard_step_size.value(),
            "rescaling_factor": self.rescaling_factor.value(),
            "second_img": self.second_img.isChecked(),
            "save_png": self.save_png.isChecked(),
            "crop_image": self.crop_image.isChecked(),
            "crop_size": self.crop_size.value(),
            "worker_num": self.worker_num.value(),
            "shape_feature": self.shape_feature.isChecked(),
            "firstorder_feature": self.firstorder_feature.isChecked(),
            "glcm_feature": self.glcm_feature.isChecked(),
            "glrlm_feature": self.glrlm_feature.isChecked(),
            "glszm_feature": self.glszm_feature.isChecked(),
            "angle_correction": self.angle_correction.isChecked(),
            "smooth_resizing": self.smooth_resizing.isChecked(),
            "first_img_dicom_transparence": self.first_img_dicom_transparence.value(),
            "first_img_overlay_dicom": self.first_img_overlay_dicom.isChecked(),
            "first_img_overlay_rois": self.first_img_overlay_rois.isChecked(),
            "first_img_overlay_rois_alpha": self.first_img_overlay_rois_alpha.value(),
            "first_img_overlay_lines": self.first_img_overlay_lines.isChecked(),
            "second_img_overlay_dicom": self.second_img_overlay_dicom.isChecked(),
            "second_img_overlay_rois": self.second_img_overlay_rois.isChecked(),
            "second_img_overlay_rois_alpha": self.second_img_overlay_rois_alpha.value(),
            "second_img_overlay_EI": self.second_img_overlay_EI.isChecked(),
            "second_img_overlay_lines": self.second_img_overlay_lines.isChecked(),
        }

        js = json.dumps(config)

        path = QFileDialog.getSaveFileName()[0]
        if not os.path.exists(path):
            return None
        with open(path if ".json" in path else path + ".json", "w+") as f:
            f.write(js)

    def load_config(self):
        path = QFileDialog.getOpenFileName()[0]
        if not os.path.exists(path):
            return None
        with open(path, "r+") as f:
            config = json.load(f)

        self.rv_name_or_nr.setText(config["rv_name_or_nr"])
        self.lv_epi_name_or_nr.setText(config["lv_epi_name_or_nr"])
        self.lv_endo_name_or_nr.setText(config["lv_endo_name_or_nr"])

        self.ventral_max.setValue(config["ventral_max"])
        self.ventral_step_size.setValue(config["ventral_step_size"])
        self.dorsal_max.setValue(config["dorsal_max"])
        self.dorsal_step_size.setValue(config["dorsal_step_size"])
        self.epicard_max.setValue(config["epicard_max"])
        self.epicard_step_size.setValue(config["epicard_step_size"])
        self.endocard_max.setValue(config["endocard_max"])
        self.endocard_step_size.setValue(config["endocard_step_size"])
        self.rescaling_factor.setValue(config["rescaling_factor"])

        self.second_img.setChecked(config["second_img"])
        self.save_png.setChecked(config["save_png"])
        self.crop_image.setChecked(config["crop_image"])
        self.crop_size.setValue(config["crop_size"])

        self.worker_num.setValue(config["ventral_max"])

        self.shape_feature.setChecked(config["shape_feature"])
        self.firstorder_feature.setChecked(config["firstorder_feature"])
        self.glcm_feature.setChecked(config["glcm_feature"])
        self.glrlm_feature.setChecked(config["glrlm_feature"])
        self.glszm_feature.setChecked(config["glszm_feature"])
        self.angle_correction.setChecked(config["angle_correction"])
        self.smooth_resizing.setChecked(config["smooth_resizing"])
        self.first_img_dicom_transparence.setValue(
            config["first_img_dicom_transparence"]
        )
        self.first_img_overlay_dicom.setChecked(config["first_img_overlay_dicom"])
        self.first_img_overlay_rois.setChecked(config["first_img_overlay_rois"])
        self.first_img_overlay_rois_alpha.setValue(
            config["first_img_overlay_rois_alpha"]
        )
        self.first_img_overlay_lines.setChecked(config["first_img_overlay_lines"])
        self.second_img.setChecked(config["second_img"])
        self.second_img_overlay_dicom.setChecked(config["second_img_overlay_dicom"])
        self.second_img_overlay_rois.setChecked(config["second_img_overlay_rois"])
        self.second_img_overlay_rois_alpha.setValue(
            config["second_img_overlay_rois_alpha"]
        )
        self.second_img_overlay_EI.setChecked(config["second_img_overlay_EI"])
        self.second_img_overlay_lines.setChecked(config["second_img_overlay_lines"])

    def create_config(self):
        cf = RunConfiguration()

        # Used number of processes
        cf.worker = self.worker_num.value()
        cf.mode = self.mode
        ###############################################
        # Image Mode Selection
        ##############################################
        cf.img_transparent = True
        cf.save_pngs = self.save_png.isChecked()
        cf.crop_img = (
            self.crop_image.isChecked()
        )  # Boolean specifying whether the image should be cropped to the heart center
        cf.crop_x = self.crop_size.value() / 100  # percent as float in range 0 - 1
        cf.crop_y = self.crop_size.value() / 100  # percent as float in range 0 - 1
        # first image
        cf.first_img_overlay_dicom = self.first_img_overlay_dicom.isChecked()
        cf.first_img_overlay_rois = self.first_img_overlay_rois.isChecked()
        cf.first_img_overlay_rois_alpha = (
            self.first_img_overlay_rois_alpha.value()
        )  # hint: float in range 0 - 1
        cf.first_img_overlay_EI = self.first_img_overlay_EI.isChecked()
        cf.first_img_overlay_lines = self.first_img_overlay_lines.isChecked()
        # second image
        cf.second_img = self.second_img.isChecked()
        cf.second_img_overlay_dicom = self.second_img_overlay_dicom.isChecked()
        cf.second_img_overlay_rois = self.second_img_overlay_rois.isChecked()
        cf.second_img_overlay_rois_alpha = (
            self.second_img_overlay_rois_alpha.value() / 100
        )  # hint: float in range 0 - 1
        cf.second_img_overlay_EI = self.second_img_overlay_EI.isChecked()
        cf.second_img_overlay_lines = self.second_img_overlay_lines.isChecked()

        ################################################
        # Calculations for the right ventricle endocard
        ###############################################
        # Indication of the name used by Circle for the contour of the right ventricle.
        cf.rv_name_or_nr = self.rv_name_or_nr.text()

        cf.rv_endo_ventral_angle_min = self.ventral_min.value()
        cf.rv_endo_ventral_angle_max = self.ventral_max.value()
        cf.rv_endo_ventral_angle_step_size = self.ventral_step_size.value()

        cf.rv_endo_dorsal_angle_min = self.dorsal_min.value()
        cf.rv_endo_dorsal_angle_max = self.dorsal_max.value()
        cf.rv_endo_dorsal_angle_step_size = self.dorsal_step_size.value()

        ################################################
        # Calculations for the left ventricular epicard
        ###############################################
        cf.lv_epi_name_or_nr = self.lv_epi_name_or_nr.text()
        cf.lv_epi_angle_min = self.epicard_min.value()
        cf.lv_epi_angle_max = self.epicard_max.value()
        cf.lv_epi_angle_step_size = self.epicard_step_size.value()

        ################################################
        # Calculations for the left ventricular epicard
        ###############################################
        cf.lv_endo_name_or_nr = self.lv_endo_name_or_nr.text()
        cf.lv_endo_angle_min = self.endocard_min.value()
        cf.lv_endo_angle_max = self.endocard_max.value()
        cf.lv_endo_angle_step_size = self.endocard_step_size.value()

        # ############################################## Resolution Settings
        # ############################################# Factor by which the read coordinates are scaled up for a more
        # precise calculation (integer between 1 and infinity). Note: The higher the resolution the longer the
        # calculation and the more RAM is needed. The script was optimized using factor 8
        cf.resize_polygon_factor = self.rescaling_factor.value()

        cf.shape_feature = self.shape_feature.isChecked()
        cf.firstorder_feature = self.firstorder_feature.isChecked()
        cf.glcm_feature = self.glcm_feature.isChecked()
        cf.glrlm_feature = self.glrlm_feature.isChecked()
        cf.glszm_feature = self.glszm_feature.isChecked()

        cf.angle_correction = self.angle_correction.isChecked()
        cf.smooth_resizing = self.smooth_resizing.isChecked()

        return cf


if __name__ == "__main__":
    freeze_support()
    multiprocessing.set_start_method("spawn")
    app = QApplication(sys.argv)

    # Add disclaimer window
    disclaimer_text = "shortCardiac is not a medical product and should only be used for scientific purposes. By clicking OK, you confirm that you understand and accept this disclaimer."
    disclaimer_reply = QMessageBox.question(None, "Disclaimer", disclaimer_text, QMessageBox.Ok | QMessageBox.Cancel)

    if disclaimer_reply == QMessageBox.Ok:
        # Load stylesheet
        file = QFile(r"dark.qss")
        file.open(QFile.ReadOnly | QFile.Text)
        steam = QTextStream(file)
        app.setStyle("QtCurve")
        app.setStyleSheet(steam.readAll())

        # Open main window
        window = MainWindow()
        window.show()

        app.exec_()
