import threading
from multiprocessing import Pool
from pathlib import Path
import tempfile
import natsort
from tkinter import Tk, Label, DoubleVar, ttk
from typing import Any, Tuple
from shortCardiacBackend import *
import os
from tqdm import tqdm

def read_last_line(file_path: Path) -> str:
    with open(file_path, "r") as file:
        lines = file.readlines()
        return lines[-1].strip() if lines else ""

class ProgressDialog(Tk):
    def __init__(self, output_path: Path):
        super().__init__()
        self.output_path = output_path
        self.max_value = 0

        self.title("Progress")
        self.geometry("400x100")

        self.label = Label(self, text="Initializing...")
        self.label.pack()

        self.progress_var = DoubleVar(self)
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=self.max_value)
        self.progress_bar.pack(expand=True, fill='both', side='top')

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_thread(self, initial_message: str):
        self.label.config(text=initial_message)

    def update_progressbar(self, max_value):
        self.max_value = max_value
        self.progress_var.set(0)
        self.progress_bar.config(maximum=max_value)

    def update_label(self, text):
        self.label.config(text=text)

    def on_close(self):
        self.quit()
        self.destroy()

    def check_updates(self):
        if not os.path.exists(self.output_path):
            self.on_close()
        try:
            last_line = read_last_line(self.output_path)
        except:
            last_line = ""
        if "%" in last_line:
            progress, message = self.parse_progress(last_line)
            self.progress_var.set(progress)
            self.update_label(message)
            if progress >= self.max_value:
                self.on_close()
                return

        self.after(1000, self.check_updates)

    def parse_progress(self, line: str) -> Tuple[int, str]:
        parts = line.split("|")
        progress = int(parts[0].strip().rstrip("%"))
        message = parts[2].strip() if len(parts) > 2 else "Processing..."
        return progress, message

def run(arg: Tuple[Any, Any, Any]) -> Any:
    print("Running process")
    if arg[2] is None:
        return None
    sCardiac = ShortCardiac(config=arg[0], dcm_file=arg[1], coords=arg[2])
    results = sCardiac.run()
    del sCardiac
    return results

def start_processing(args, output_path, config, dcm_folder, progress_dialog):
    progress_dialog.update_label("Processing...")
    with open(output_path, "w") as file:
        if config.worker == 0:
            results = [run(arg) for arg in tqdm(args, file=file)]
        else:
            with Pool(config.worker) as pool:
                results = [_ for _ in tqdm(pool.imap_unordered(run, args), total=len(args), file=file)]
        results = natsort.natsorted(results)
        save(results, dcm_folder)
    os.remove(output_path)

def main(coord_file: str, dcm_folder: Path, config: Any) -> None:
    output_path = Path(tempfile.gettempdir()) / "shortcardiac.txt"

    if output_path.exists():
        os.remove(output_path)
    output_path.touch()

    progress_dialog = ProgressDialog(output_path=output_path)
    progress_dialog.update_label("Loading DICOM files...")

    # Hauptlogik in einem separaten Thread
    def main_logic(coord_file):
        dicoms, UIs = load_DICOMs(dcm_folder)

        coordReader = CoordReader(config)
        if not coord_file.endswith(".pkl"):
            progress_dialog.update_label("Prepare Coordinates...")
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

        coords = coordReader.load_coordinates(coord_file)
        args = parse_to_arguments(config, coords, dicoms, UIs)

        progress_dialog.update_progressbar(len(args))
        progress_dialog.check_updates()

        threading.Thread(target=start_processing, args=(args, output_path, config, dcm_folder, progress_dialog)).start()

    threading.Thread(target=main_logic, args=(coord_file,)).start()
    progress_dialog.mainloop()
