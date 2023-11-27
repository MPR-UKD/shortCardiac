from pathlib import Path

from main import *
from shortCardiacBackend import RunConfiguration


def run(arg, slice):
    if arg[2] is None:
        return None
    if slice is not None:
        if Path(arg[1]).name != slice:
            return None
    else:
        print(Path(arg[1]).name)
    sCardiac = ShortCardiac(config=arg[0], dcm_file=arg[1], coords=arg[2])
    results = sCardiac.run()
    del sCardiac
    return results


if __name__ == "__main__":
    # With this script you can test the function of shortCardiac.
    # The calculated parameters can be found in TestData/DICOM/*
    coord_file = r"C:\Users\ludge\PycharmProjects\shortCardiac\Proband201\Proband201_gesamteVolumetrie_fuerSeptumReferenz_20231117-1422.cvi42wsx.pkl"
    dcm_folder = r"C:\Users\ludge\PycharmProjects\shortCardiac\Proband201\12_mpi82_bSSFP_10min_SA20_FOV320_16x8mm_30fps_Volumetrie"
    config = RunConfiguration()

    coord_reader = CoordReader(config)
    #coord_reader.preparation_cvi42(coord_file)
    coords = coord_reader.load_coordinates(coord_file)

    # Reading in the coordinates
    dicoms, UIs = load_DICOMs(dcm_folder)


    args = parse_to_arguments(config, coords, dicoms, UIs)
    results = [run(arg, None) for arg in tqdm(args)]
