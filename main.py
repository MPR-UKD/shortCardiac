import threading
import time
from multiprocessing import Pool, freeze_support
from pathlib import Path
import tempfile
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

def read_last_line(file_path):
    with open(file_path, "r") as file:
        line = [_ for _ in file.readlines()]
        try:
            return line[-1].split(r"\n,")[-1]
        except IndexError:
            return ""

def main(coord_file, dcm_folder, config, update_progress=None):
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

    output_path = Path(tempfile.gettempdir()) / "dicom_translator.txt"
    with open(output_path, "w") as file:
        pass

    def check_progress():
        while True:
            last_line = read_last_line(output_path)
            if "%" in last_line:
                progress = int(last_line.split("/")[0].split("|")[-1])
                update_progress(progress)
                if progress == len(args):
                    break
            time.sleep(0.1)
    if update_progress is not None:
        update_progress(len(args))
        progress_checker = threading.Thread(target=check_progress, daemon=True)
        progress_checker.start()

    with open(output_path, "w+") as file:
        if config.worker == 0:
            results = [run(arg) for arg in tqdm(args, file=file)]
        else:
            with Pool(config.worker) as pool:
                results = [_ for _ in tqdm(pool.imap_unordered(run, args), total=len(args), file=file)]

    results = natsort.natsorted(results)
    save(results, dcm_folder)
