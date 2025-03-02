import os
import sys
from dataclasses import dataclass
from datetime import datetime
from glob import glob
from os.path import join
import numpy as np # type: ignore
from src.toolbox import Protocol
from tqdm import tqdm

sys.path.append("/Users/MA_Arash/MA_git/EIT_Thigh_Force_Estimation")

@dataclass
class SingleEitFrame:
    """Class to store a single frame of EIT measurement data."""
    setup_name: str = ""
    f_scale: str = ""


# List of header keys for .eit file parsing
HEADER_KEYS = [
    "number_of_header", "file_version_number", "setup_name", "date_time",
    "f_min", "f_max", "f_scale", "f_count", "current_amplitude", "framerate",
    "phase_correct_parameter", "unknown_1", "unknown_2", "unknown_3",
    "unknown_4", "unknown_5", "MeasurementChannels",
    "MeasurementChannelsIndependentFromInjectionPattern"
]


def list_eit_files(path: str) -> list:
    """
    Returns a sorted list of all .eit files in the given directory.

    Parameters
    ----------
    path : str
        Path to the directory

    Returns
    -------
    list
        Sorted list of .eit file names
    """
    try:
        return np.sort([f for f in os.listdir(path) if f.endswith(".eit")])
    except FileNotFoundError:
        print(f"Error: Directory not found - {path}")
        return []
    except Exception as e:
        print(f"Error listing .eit files in {path}: {e}")
        return []


def parse_eit_file_content(read_content: list) -> SingleEitFrame:
    """
    Parses a single .eit file's content and returns an EIT frame object.

    Parameters
    ----------
    read_content : list
        List of strings containing the .eit file content

    Returns
    -------
    SingleEitFrame
        Parsed EIT frame object
    """
    frame = SingleEitFrame()

    # Assign header values
    for content, key in zip(read_content, HEADER_KEYS):
        setattr(frame, key, content)

    frame.f_scale = "linear" if frame.f_scale == "0" else "logarithmic"

    # Parse EIT measurement data
    for i in range(len(HEADER_KEYS), len(read_content) - 1, 2):
        el_cmb = "_".join(read_content[i].split())
        lct = [float(ele.replace("E", "e")) for ele in read_content[i + 1].split("\t")]
        fin_val = np.array([complex(lct[j], lct[j + 1]) for j in range(0, len(lct), 2)])

        setattr(frame, el_cmb, fin_val)

    return frame


def process_eit_files(target_path: str, skip: int = 5, n_el: int = 16):
    """
    Processes .npz files, modifies electrode pairings, and updates data.

    Parameters
    ----------
    target_path : str
        Path to the directory containing .npz files
    skip : int, optional
        Number of electrodes to skip in pairing (default is 5)
    n_el : int, optional
        Total number of electrodes (default is 16)

    Returns
    -------
    None
    """
    filepaths = np.sort(glob(f"{target_path}/*.npz"))
    for filepath in tqdm(filepaths, desc="Processing EIT .npz files", unit="file"):
        tmp_eit = np.load(filepath, allow_pickle=True)

        els = np.arange(1, n_el + 1)
        matrix = np.zeros((n_el, n_el), dtype=complex)

        for i1, i2 in zip(els, np.roll(els, -(skip + 1))):
            matrix[i1 - 1, :n_el] = tmp_eit[f"{i1}_{i2}"][:n_el]

        np.savez(filepath, eit=matrix, timestamp=convert_timestamp(tmp_eit["date_time"].tolist()))


def convert_eit_directory_to_npz(input_path: str, protocol: Protocol, output_path: str = None):
    """
    Converts all .eit files in a directory to .npz format.

    Parameters
    ----------
    input_path : str
        Directory containing .eit files
    protocol : Protocol
        Measurement protocol object
    output_path : str, optional
        Directory to save .npz files 

    Returns
    -------
    None
    """
    output_path = output_path or join(input_path, "eit_processed")
    os.makedirs(output_path, exist_ok=True)

    try:
        file_path = join(glob(f"{input_path}/eit_raw/2025*")[0], "setup/")
    except IndexError:
        print(f"Error: No EIT raw data found in {input_path}")
        return

    eit_files = list_eit_files(file_path)
    if len(eit_files) == 0:
        print(f"No .eit files found in {input_path}")
        return

    print("Converting .eit to .npz...")
    for filename in eit_files:
        filepath = join(file_path, filename)

        try:
            with open(filepath, "r") as file:
                read_content = file.read().split("\n")
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            continue

        frame = parse_eit_file_content(read_content)
        save_filepath = join(output_path, f"{frame.setup_name}.npz")
        np.savez(save_filepath, **frame.__dict__)
        print(f"Saved: {save_filepath}")

    print("Reshaping .npz data...")
    process_eit_files(target_path=output_path, skip=protocol.EITMeasurement.injection_skip, n_el=protocol.EITMeasurement.n_el)


def convert_timestamp(date_str: str):
    """
    Converts date string to a timestamp.

    Parameters
    ----------
    date_str : str
        Date in the format "YYYY.MM.DD. HH:MM:SS.FFF"

    Returns
    -------
    float or str
        Converted timestamp or formatted datetime string
    """
    try:
        if len(str(date_str).split(".")) > 2:
            return datetime.strptime(date_str, "%Y.%m.%d. %H:%M:%S.%f").timestamp()
        else:
            return datetime.fromtimestamp(float(date_str)).strftime("%Y.%m.%d. %H:%M:%S.%f")
    except Exception as e:
        print(f"Error converting timestamp: {e}")
        return date_str
