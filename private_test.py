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
    coord_file = r"C:\Users\ludge\Downloads\fehlerhafte Datensätze\fehlerhafte Datensätze\Proband203_fehlerhafter Datensatz\Proband203_fehlerhafter Datensatz\Proband203_Workspace_mv_Slice17_20221208.cvi4.pkl"
    dcm_folder = r"C:\Users\ludge\Downloads\fehlerhafte Datensätze\fehlerhafte Datensätze\Proband203_fehlerhafter Datensatz\Proband203_fehlerhafter Datensatz\Slice17"
    config = RunConfiguration()

    # Reading in the coordinates
    dicoms, UIs = load_DICOMs(dcm_folder)
    coordReader = CoordReader(config)
    coords = coordReader.load_coordinates(coord_file)

    args = parse_to_arguments(config, coords, dicoms, UIs)
    results = [run(arg, "scan456.dcm") for arg in tqdm(args)]
