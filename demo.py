from shortCardiacBackend import *
from multiprocessing import Pool
from tqdm import tqdm


def calculation(arguments):
    cf, dcm_file, coord_dict = arguments
    sCardiac = ShortCardiac(config=cf, dcm_file=dcm_file, coords=coord_dict)
    return sCardiac.run()


if __name__ == "__main__":
    # Specification of the locally stored file paths
    cvi42_file = r"local_path_to_cvi42_file_with_segmentations.cvi42wsx"
    dcm_folder = r"local_path_to_dicom_data"
    coord_file = r"local_path_name_of_dict_with_contours_after_preprocessing"

    # Create the RunConfiguration - here you define what should be calculated
    config = RunConfiguration()

    # Scanning the Dicom data
    dicom_files, UIs = load_DICOMs(dcm_folder)

    # Importing and preparing the coordinates using an example for Cvi42
    coordReader = CoordReader(config)
    coordReader.preparation_cvi42(cvi42_file=cvi42_file, save_file_name=coord_file)
    coords = coordReader.load_coordinates(coord_file)

    # Parallel evaluation of the images
    with Pool(8) as pool:
        args = parse_to_arguments(config, coords, dicom_files, UIs)
        results = [
            _ for _ in tqdm(pool.imap_unordered(calculation, args), total=len(args))
        ]

    # Saves the results as csv-file
    save(results, dcm_folder)
