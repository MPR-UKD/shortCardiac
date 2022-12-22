import time
from multiprocessing import Pool, freeze_support

import natsort
from tqdm import tqdm

from shortCardiacBackend import *


def run(arg):
    if arg[2] is None:
        return None
    sCardiac = ShortCardiac(config=arg[0], dcm_file=arg[1], coords=arg[2])
    results = sCardiac.run()
    del sCardiac
    return results


def main(coord_file, dcm_folder, config):
    # Reading in the Dicom images
    dicoms, UIs = load_DICOMs(dcm_folder)
    # Transformation of the coordinates into a file format optimized for shortCardiac Notes: Conversion can take
    # longer depending on the size, but conversion is only necessary for the first calculation. If the data has
    # already been converted, this step can be skipped.
    coordReader = CoordReader(config)
    if not coord_file.endswith(".pkl"):
        if config.mode == "cvi42":
            cvi42_file = coord_file
            coord_file = coord_file[:-4] + ".pkl"
            coordReader.preparation_cvi42(
                cvi42_file=cvi42_file, save_file_name=coord_file
            )
        elif config.mode == "nii":
            nii_file = coord_file
            coord_file = (
                coord_file[:-4] + ".pkl"
                if "nii.gz" not in coord_file
                else coord_file[:-7] + ".pkl"
            )
            coordReader.preparation_nii(
                nii_file=nii_file, dcm_sorted=dicoms, save_file_name=coord_file
            )
        else:
            raise UserWarning

    # Reading in the coordinates
    coords = coordReader.load_coordinates(coord_file)

    args = parse_to_arguments(config, coords, dicoms, UIs)

    if config.worker == 0:
        results = [run(arg) for arg in tqdm(args)]
    else:
        with Pool(config.worker) as pool:
            results = [_ for _ in tqdm(pool.imap_unordered(run, args), total=len(args))]

    results = natsort.natsorted(results)
    save(results, dcm_folder)
