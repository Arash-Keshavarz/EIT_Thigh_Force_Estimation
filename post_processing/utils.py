
import os
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from glob import glob

@dataclass
class SingleEitFrame:
    setup_name: str = ""
    f_scale: str = ""

header_keys = [
    "number_of_header",
    "file_version_number",
    "setup_name",
    "date_time",
    "f_min",
    "f_max",
    "f_scale",
    "f_count",
    "current_amplitude",
    "framerate",
    "phase_correct_parameter",
    "uknwn_1",  # TBD: Sadly an unknown parameter.
    "uknwn_2",  # TBD: Sadly an unknown parameter.
    "uknwn_3",  # TBD: Sadly an unknown parameter.
    "uknwn_4",  # TBD: Sadly an unknown parameter.
    "uknwn_5",  # TBD: Sadly an unknown parameter.
    "MeasurementChannels",
    "MeasurementChannelsIndependentFromInjectionPattern",
]

def list_eit_files(path: str) -> list:
    """
    Returns a list of all .eit files in the directory path.

    Parameters
    ----------
    path : str
        Path to the directory

    Returns
    -------
    list
        list of files with .eit ending
    """
    try:
        src_list = [_ for _ in os.listdir(path) if _.endswith(".eit")]
        return src_list
    except Exception as e:
        print(f"Error listing .eit files in directory: {path}. Error: {e}")
        return []

def doteit_in_SingleEitFrame(read_content: list) -> SingleEitFrame:
    """
    Returns single object without saving anything.

    Parameters
    ----------
    read_content : list
        Content of the .eit file as a list of strings

    Returns
    -------
    SingleEitFrame
        Object representing the parsed .eit data
    """
    frame = SingleEitFrame()

    # Populate frame with header information
    for content, key in zip(read_content, header_keys):
        setattr(frame, key, content)
    
    frame.f_scale = "linear" if frame.f_scale == "0" else "logarithmic"

    # Populate frame with data
    for i in range(len(header_keys), len(read_content) - 1, 2):
        el_cmb = read_content[i].split(" ")
        el_cmb = f"{el_cmb[0]}_{el_cmb[1]}"
        lct = read_content[i + 1].split("\t")
        lct = [ele.replace("E", "e") for ele in lct]
        lct = [float(ele) for ele in lct]
        fin_val = np.zeros(len(lct) // 2, dtype=complex)
        for idx, cmpl in enumerate(range(0, len(lct), 2)):
            fin_val[idx] = complex(lct[cmpl], lct[cmpl + 1])
        setattr(frame, el_cmb, np.array(fin_val))
    
    return frame

def convert_fulldir_doteit_to_npz(lpath: str, spath: str) -> None:
    """
    Converts all .eit files in a directory to .npz files in a directory spath.

    Parameters
    ----------
    lpath : str
        Path to load .eit files from
    spath : str
        Path to save .npz files

    Returns
    -------
    None
    """
    os.makedirs(spath, exist_ok=True)  # Ensure the save path exists

    objects = list_eit_files(lpath)
    if not objects:
        print(f"No .eit files found in directory: {lpath}")
        return

    for obj in objects:
        fname = os.path.join(lpath, obj)
        with open(fname, "r") as file:
            read_content = file.read().split("\n")

        frame = doteit_in_SingleEitFrame(read_content)
        save_path = os.path.join(spath, f"{frame.setup_name}.npz")
        np.savez(save_path, **(frame.__dict__))
        print(f"Saved: {save_path}")




def convert_timestamp(date_str):
    if len(str(date_str).split(".")) > 2:
        timestamp = datetime.strptime(date_str, "%Y.%m.%d. %H:%M:%S.%f")
        return timestamp.timestamp()
    else:
        date_time = datetime.fromtimestamp(float(date_str))
        return date_time.strftime("%Y.%m.%d. %H:%M:%S.%f")
    


def process_eit_files(tar_path, skip=5, n_el=16):

    """
    Process EIT files in the given directory, adjusts electrode pairings, and saves updated data.
    
    Parameters:
    - tar_path (str): Path to the directory containing the .npz files.
    - skip (int): Number of electrodes to skip in pairing. Default is 5.
    - n_el (int): Total number of electrodes. Default is 16.

    Returns:
    - None
    """

    for ele in glob(f"{tar_path}/*.npz"):
        tmp_eit = np.load(ele, allow_pickle= True)

        els = np.arange(1, n_el+1)
        mat = np.zeros((n_el, n_el), dtype=complex)

        for i1, i2 in zip(els, np.roll(els, -(skip+1))):
            mat[i1 - 1, :n_el] = tmp_eit[f"{i1}_{i2}"][:n_el]

        np.savez(
        ele,
        eit=mat,
        timestamp=convert_timestamp(tmp_eit["date_time"].tolist()),
    )
