from main import main
from shortCardiacBackend import RunConfiguration

if __name__ == "__main__":
    # With this script you can test the function of shortCardiac.
    # The calculated parameters can be found in TestData/DICOM/*
    nii_file = r"TestData/mask.nii.gz"
    dcm_folder = r"TestData/Dicom"
    config = RunConfiguration()

    config.rv_name_or_nr = "1"
    config.lv_epi_name_or_nr = "2"
    config.lv_endo_name_or_nr = "3"

    main(nii_file, dcm_folder, config)
