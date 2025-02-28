"""
post_processing.py
------------------

This module provides functions and classes to post‐process IsoForce and IsoForcePy data.
It includes functions for filtering, scaling, edge detection, and segment extraction,
as well as classes to wrap these operations for specific data formats.
"""

import os
import re
from datetime import datetime, timedelta
from typing import Any, List, Tuple, Union, Dict, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, find_peaks, resample

def resample_signals(iso_iso, iso_py, target_length=None):
    iso_iso = np.asarray(iso_iso)
    iso_py = np.asarray(iso_py)
    if target_length:
        print(f"Resample both signals to a length of {target_length} samples.")
        iso_py = resample(iso_py, num=target_length)
        iso_iso = resample(iso_iso, num=target_length)
        return iso_iso, iso_py
    else:
        target_length = max(len(iso_iso), len(iso_py))
        print(f"Resample both signals to a length of {target_length} samples.")
        if len(iso_iso) > len(iso_py):
            iso_py = resample(iso_py, num=target_length)
        elif len(iso_py) > len(iso_iso):
            iso_iso = resample(iso_iso, num=target_length)
        return iso_iso, iso_py


def detect_shift(signal1, signal2):
    N = max(len(signal1), len(signal2))
    corr = np.correlate(signal1, signal2, mode="full")
    lags = np.arange(-N + 1, N)

    max_corr_idx = np.argmax(corr)
    discrete_time_shift = lags[max_corr_idx]
    print(f"Discrete time shift of {discrete_time_shift}.")
    return discrete_time_shift

def lowpass_filter(
    data: Union[np.ndarray, List[float]], cutoff: float = 2.0, fs: float = 100.0, order: int = 4
) -> np.ndarray:
    """
    Apply a low-pass Butterworth filter to the input signal.

    Parameters
    ----------
    data : array-like
        The input signal.
    cutoff : float, optional
        The cutoff frequency in Hz (default is 2.0).
    fs : float, optional
        The sampling rate in Hz (default is 100.0).
    order : int, optional
        The order of the filter (default is 4).

    Returns
    -------
    np.ndarray
        The filtered signal.
    """
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    filtered_signal = filtfilt(b, a, np.asarray(data))
    return filtered_signal

def scale_to_range(
    values: Union[np.ndarray, List[float], Tuple[float, ...]], new_min: float = 0.0, new_max: float = 1.0
) -> Union[np.ndarray, List[float], Tuple[float, ...]]:
    """
    Scale input value(s) from their original range to a new specified range [new_min, new_max].

    Parameters
    ----------
    values : float, list, tuple, or np.ndarray
        Input value(s) to scale.
    new_min : float, optional
        The lower bound of the new range (default is 0.0).
    new_max : float, optional
        The upper bound of the new range (default is 1.0).

    Returns
    -------
    float, list, tuple, or np.ndarray
        Scaled value(s) within the specified range.
        The return type matches the input type.
    """
    values_arr = np.asarray(values)
    old_min = np.min(values_arr)
    old_max = np.max(values_arr)

    # Avoid division by zero if old_max equals old_min
    if old_max == old_min:
        scaled = np.full_like(values_arr, new_min)
    else:
        scaled = new_min + (values_arr - old_min) * (new_max - new_min) / (old_max - old_min)

    # Return the same type as the input if possible.
    if isinstance(values, (list, tuple)):
        return type(values)(scaled.tolist())
    return scaled


def edge_detection(signal: Union[np.ndarray, List[float]], mode: str = "rising", threshold: float = 1.0) -> np.ndarray:
    """
    Detect edges (rising or falling) in a signal based on a specified threshold.

    Parameters
    ----------
    signal : array-like
        The input signal.
    mode : {"rising", "falling"}, optional
        The type of edge to detect. For "rising", detects edges where the difference equals threshold;
        for "falling", where the difference equals -threshold (default is "rising").
    threshold : float, optional
        The difference value that defines an edge (default is 1.0).

    Returns
    -------
    np.ndarray
        The indices of the detected edges in the signal.
    """
    signal = np.asarray(signal)
    diff = np.diff(signal)
    if mode == "rising":
        edges = np.where(diff == threshold)[0]
    elif mode == "falling":
        edges = np.where(diff == -threshold)[0]
    else:
        raise ValueError('mode must be either "rising" or "falling"')
    return edges

def convert_timestamp(date_str: Union[str, float]) -> Union[float, str]:
    """
    Convert a timestamp string to a UNIX timestamp or vice versa.

    Parameters
    ----------
    date_str : str or float
        The date string or UNIX timestamp.

    Returns
    -------
    float or str
        The converted timestamp.
    """
    date_str = str(date_str)
    if len(date_str.split(".")) > 2:
        timestamp = datetime.strptime(date_str, "%Y.%m.%d. %H:%M:%S.%f")
        return timestamp.timestamp()
    else:
        date_time = datetime.fromtimestamp(float(date_str))
        return date_time.strftime("%Y.%m.%d. %H:%M:%S.%f")
        
def generate_DF(file_path: str, output_path: str) -> pd.DataFrame:
    """
    Convert raw ISO data from a .txt file( which are messy) into a cleaned DataFrame and save it as a .csv file.

    The function reads a tab-delimited file containing columns for torque, angle, and velocity,
    cleans the data by replacing commas with periods and coercing numeric types, and then saves the cleaned
    data to a CSV file.

    Parameters
    ----------
    file_path : str
        Path to the input .txt file containing raw ISO data.
    output_path : str
        Path where the cleaned data CSV file will be saved.

    Returns
    -------
    pd.DataFrame
        A cleaned DataFrame with columns "Torque", "Angle", and "Velocity".
    """
    iso_data = pd.read_csv(file_path, delimiter="\t", header=0)

    # Clean and convert the "Torque" column.
    torque_str = iso_data["Torque (or Velocity - ISOT, or Force - CKC)"].str.replace(",", ".", regex=False)
    torque_clean = pd.to_numeric(torque_str, errors="coerce").dropna()

    # Clean and convert the "Angle" column.
    angle_str = iso_data["Angle (or Distance - CKC)"].str.replace(",", ".", regex=False)
    angle_clean = pd.to_numeric(angle_str, errors="coerce").dropna()

    # Clean and convert the "Velocity" column.
    velocity_str = iso_data["Velocity (or Torque - ISOT, or Force - CKC)"].str.replace(",", ".", regex=False)
    velocity_clean = pd.to_numeric(velocity_str, errors="coerce").dropna()

    iso_raw_df = pd.DataFrame({
        "Torque": torque_clean,
        "Angle": angle_clean,
        "Velocity": velocity_clean
    })

    iso_raw_df.to_csv(output_path, index=False)
    print(f"Cleaned data saved to {output_path}")

    return iso_raw_df


class IsoForceRAW:

    """
    Post-process IsoForce kinetic data acquired from the original device.

    This class applies filtering, edge detection, and segmentation to the raw data.
    """

    def __init__(self, DF: pd.DataFrame, LP_filter_enabled: bool = False, Leg: str= "right") -> None:
        """
        Initialize the IsoForceRAW processor.

        Parameters
        ----------
        DF : pd.DataFrame
            DataFrame containing raw "Torque", "Angle", and "Velocity" data.
        LP_filter_enabled : bool, optional
            Whether to apply a low-pass filter to the torque and angle data (default is False).
        """

        self.DF = DF
        self.LP_filter_enabled = LP_filter_enabled
        self.leg = Leg
        self.init_data()
        self.detect_start_stop_idxs()
        self.export_segments()
        self.filter_torque()


    def init_data(self) -> None:
        """Extract raw data from the DataFrame and apply filtering if enabled."""
        if self.leg == "right":
            self.torque_raw = self.DF["Torque"]
            self.angle_raw = self.DF["Angle"]
            self.speed = self.DF["Velocity"]
        else:
            self.torque_raw = -1 * self.DF["Torque"]
            self.angle_raw = self.DF["Angle"]
            self.speed = self.DF["Velocity"]

        if self.LP_filter_enabled:
            print("Applying low-pass filter to torque and angle data.")
            self.torque = lowpass_filter(self.torque_raw)
            self.angle = lowpass_filter(self.angle_raw, cutoff=2, fs=400) # fs of isoforce = 400
        else:
            self.torque = self.torque_raw
            self.angle = self.angle_raw


    def detect_start_stop_idxs(self) -> None:
        """
        Detect start and stop indices using the gradient of the speed signal.

        The indices are determined based on where the speed gradient exceeds the mean
        or is less than the negative mean. Segments shorter than 1000 samples or longer than
        2500 samples are excluded.
        """
        k = np.arange(len(self.speed))
        dx_dk = np.gradient(self.speed, k)
        self.start_idxs = np.where(dx_dk > np.mean(dx_dk))[0][1::2]
        self.stop_idxs = np.where(dx_dk < -np.mean(dx_dk))[0][::2]

        # Exclude segments that are too short (<1000 samples) or too long (>2500 samples)
        too_short = np.where(self.stop_idxs - self.start_idxs < 1000)[0]
        too_long = np.where(self.stop_idxs - self.start_idxs > 2500)[0]
        cut_out = np.concatenate([too_short, too_long])
        self.start_idxs = np.delete(self.start_idxs, cut_out)
        self.stop_idxs = np.delete(self.stop_idxs, cut_out)       


    def export_segments(self) -> None:
        """
        Export data segments based on the detected start and stop indices.

        The function creates dictionaries of torque and angle segments and also builds
        an exclusion window (a binary mask) over the full data length.
        """
        T_segment_dict: Dict[str, np.ndarray] = {}
        A_segment_dict: Dict[str, np.ndarray] = {}
        exclude_window = np.zeros(len(self.speed))
        for idx, (start, stop) in enumerate(zip(self.start_idxs, self.stop_idxs)):
            T_segment_dict[f"T_seg_{idx}"] = self.torque[start:stop]
            A_segment_dict[f"A_seg_{idx}"] = self.angle[start:stop]
            exclude_window[start:stop] = 1
        self.torque_segments = T_segment_dict
        self.angle_segments = A_segment_dict
        self.exclude_window = exclude_window

    def filter_torque(self) -> None:
        """Apply the exclusion window to the torque signal."""
        self.torque = self.torque * self.exclude_window


    def plot_torque(self) -> None:
        """Plot the filtered torque signal alongside the raw torque."""
        tks = np.round(np.linspace(np.min(self.torque), np.max(self.torque), 5))
        plt.figure(figsize=(12, 3))
        plt.plot(self.torque, "C0", label="Filtered Torque")
        plt.plot(self.torque_raw, "C8", lw=0.5, label="Raw Torque")
        plt.grid(True)
        plt.legend()
        plt.xlabel("Sample index (k)")
        plt.ylabel("Torque (Nm)")
        plt.show()

    def plot_angle(self) -> None:
        """Plot the angle signal."""
        plt.figure(figsize=(12, 3))
        plt.plot(self.angle, "C3")
        plt.grid(True)
        plt.xlabel("Sample index (k)")
        plt.ylabel("Angle (°)")
        plt.show()

    def plot_speed(self) -> None:
        """Plot the speed signal with markers for start and stop indices."""
        plt.figure(figsize=(12, 3))
        plt.plot(self.speed, "C8", label="Speed")
        plt.scatter(self.start_idxs, self.speed[self.start_idxs], c="C2", label="Start idx")
        plt.scatter(self.stop_idxs, self.speed[self.stop_idxs], c="C3", label="Stop idx")
        plt.grid(True)
        plt.xlabel("Sample index (k)")
        plt.ylabel("Speed (°/s)")
        plt.legend(loc="upper left")
        plt.show()

    def plot_data(self, filename: Optional[str] = None) -> None:
        """
        Plot torque, angle, and speed signals along with start and stop markers.

        Parameters
        ----------
        filename : str, optional
            If provided, the figure will be saved to this file.
        """
        plt.figure(figsize=(12, 3))
        plt.plot(self.torque, "C0", label="Torque")
        plt.plot(self.angle, "C3", label="Angle")
        plt.plot(self.speed, "C8", label="Speed")
        plt.scatter(self.start_idxs, self.speed[self.start_idxs], c="C2", label="Start idx")
        plt.scatter(self.stop_idxs, self.speed[self.stop_idxs], c="C4", label="Stop idx")
        plt.xlabel("Sample index (k)")
        plt.grid(True)
        plt.legend(loc="upper left")
        if filename:
            plt.tight_layout()
            plt.savefig(filename)
        plt.show()


###############################
# Class for processing IsoData from NI chip

def extract_timestamp_and_sample(filename: str) -> Tuple[Optional[datetime], Optional[int]]:
    """
    Extract a timestamp and sample number from the filename.

    The filename is expected to match the pattern:
        _YYYY-MM-DD_HH-MM-SS_<sample number>.npz

    Parameters
    ----------
    filename : str
        The filename to parse.

    Returns
    -------
    tuple
        A tuple (timestamp, sample_number) where timestamp is a datetime object and sample_number is an integer.
        Returns (None, None) if the filename does not match the expected format.
    """
    match = re.search(r"_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_(\d+)\.npz$", filename)
    if match:
        timestamp_str = match.group(1)
        sample_number = int(match.group(2))
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
        return timestamp, sample_number
    return None, None



class IsoForcePy:
    """
    Process IsoForce data acquired from a Python script recorded by NI card.

    This class loads .npz files from a specified directory, aggregates and processes the data,
    applies filtering and scaling, and segments the signals.
    """
    def __init__(
        self,
        path: str,
        Leg : str = "right",
        LP_filter_enabled: bool = True,
        over_UTC: bool = False,
        scale_0_1: bool = True,
        speed_window_trunc: bool = True,
        phase_shift: int = 0,
        distance: int = 500,
    ) -> None:
        """
        Initialize the IsoForcePy processor.

        Parameters
        ----------
        path : str
            Path to the directory containing raw .npz files.
        Leg : str
            Leg of test subjects
        LP_filter_enabled : bool, optional
            Whether to low-pass filter the torque data (default is True).
        over_UTC : bool, optional
            Whether to plot using UTC timestamps (default is False).
        scale_0_1 : bool, optional
            Whether to scale all analog values between 0 and 1 (default is True).
        speed_window_trunc : bool, optional
            Whether to create a speed window mask (default is True).
        phase_shift : int, optional
            Time index phase shift between IsoForce and Python data (heuristic, default is 0).
        """
        self.path = path
        self.Leg = Leg
        self.LP_filter_enabled = LP_filter_enabled
        self.over_UTC = over_UTC
        self.scale_0_1 = scale_0_1
        self.speed_window_trunc = speed_window_trunc
        self.phase_shift = phase_shift

        self.init_data()
        self.export_segments(distance=distance)
        self.filter_torque()

    def init_data(self) -> None:
        """Load and aggregate data from .npz files in the given directory."""
        angle: List[float] = []   # Channel 1
        torque: List[float] = []  # Channel 2
        speed: List[float] = []   # Channel 3
        timestamps_list: List[datetime] = []
        timestmp_current : List[datetime] = []

        file_list = sorted(
            [f for f in os.listdir(self.path) if f.endswith(".npz")],
            key=lambda f: extract_timestamp_and_sample(f),
        )

        # Keep only the last file for each unique timestamp.
        last_file_for_timestamp: Dict[datetime, str] = {}
        for file_name in file_list:
            timestamp, sample_number = extract_timestamp_and_sample(file_name)
            if timestamp is not None:
                last_file_for_timestamp[timestamp] = file_name

        for timestamp, last_file in last_file_for_timestamp.items():
            file_path = os.path.join(self.path, last_file)
            data = np.load(file_path, allow_pickle=True)
            ch_1, ch_2, ch_3 = data["data"]
            assert len(ch_1) == len(ch_2) == len(ch_3), "Channel lengths do not match."

            sampling_rate = data["sampling_rate"]
            time_current = data["timestamps_current"]
            # Expand timestamps for each sample.
            timestamps_expanded = [
                timestamp + timedelta(seconds=(i / sampling_rate)) for i in range(len(ch_1))
            ]

            angle.extend(ch_1)
            torque.extend(ch_2)
            speed.extend(ch_3)
            timestamps_list.extend(timestamps_expanded)
            timestmp_current.extend(time_current)

        if self.Leg == "right":
            self.angle = np.array(angle)
            self.torque_raw = np.array(torque)
            self.speed = np.array(speed)
        else:
            self.angle = -1 * np.array(angle)
            self.torque_raw = -1 * np.array(torque)
            self.speed = -1 * np.array(speed)


        if self.LP_filter_enabled:
            self.torque = lowpass_filter(self.torque_raw)
        else:
            self.torque = self.torque_raw

        if self.scale_0_1:
            self.angle = scale_to_range(self.angle)
            self.torque = scale_to_range(self.torque)
            self.torque_raw = scale_to_range(self.torque_raw)
            self.speed = scale_to_range(self.speed)

        if self.speed_window_trunc:
            speed_window = np.copy(self.speed)
            # Create a binary mask: set values to 1 if above a threshold, else 0.
            speed_window[speed_window <= 0.95] = 0
            speed_window[speed_window > 0.5] = 1

            # Add a few zeros at the beginning
            num_zeros = 10  
            speed_window = np.concatenate((np.zeros(num_zeros), speed_window))
            self.speed_window = speed_window

        if self.over_UTC:
            self.time = np.array(timestamps_list)
        else:
            self.time = np.arange(len(timestamps_list))

    def export_segments(self, distance: int = 500, height: float = 0.7) -> None:
        """
        Segment the data based on detected peaks and edges.

        The stop indices are determined by finding peaks in the angle signal.
        The start indices are determined using edge detection on the speed signal,
        and are adjusted by the phase shift parameter.

        Parameters
        ----------
        distance : int, optional
            Minimum horizontal distance (in samples) between peaks (default is 500).
        height : float, optional
            Minimum height of peaks (default is 0.7).
        """
        T_segment_dict: Dict[str, np.ndarray] = {}
        A_segment_dict: Dict[str, np.ndarray] = {}

        self.stop_idxs, _ = find_peaks(self.angle, distance=distance, height=height) # for tst remove 1 element
        #self.stop_idxs = self.stop_idxs[1:]  # -> for those that we dont have the first segment
        ##########
        start_detected = edge_detection(self.speed_window, mode="rising")
        
        # Compute differences between consecutive indices
        diffs = np.diff(start_detected)

        # Keep the first index and then only those where the difference is > 400
        valid_indices = np.insert(np.where(diffs > 400)[0] + 1, 0, 0)

        # Filtered start indices
        start_detected = start_detected[valid_indices]
        start_filt = []
        for stop in self.stop_idxs:
            diff = stop - start_detected
            positive_diffs = diff[diff > 0]
            if positive_diffs.size == 0:
                continue
            min_diff_idx = np.argmin(positive_diffs)
            start_filt.append(start_detected[diff > 0][min_diff_idx])

        self.start_idxs = np.array(start_filt) - self.phase_shift

        # Exclude segments shorter than 300 samples (~3 seconds at fs=300).
        valid_mask = (self.stop_idxs - self.start_idxs) > 300
        self.start_idxs = self.start_idxs[valid_mask]
        self.stop_idxs = self.stop_idxs[valid_mask]

        assert self.start_idxs.shape == self.stop_idxs.shape, "start_idxs and stop_idxs do not match."

        exclude_window = np.zeros(len(self.torque))
        for idx, (start, stop) in enumerate(zip(self.start_idxs, self.stop_idxs)):
            T_segment_dict[f"T_seg_{idx}"] = self.torque[start:stop]
            A_segment_dict[f"A_seg_{idx}"] = self.angle[start:stop]
            exclude_window[start:stop] = 1

        self.torque_segments = T_segment_dict
        self.angle_segments = A_segment_dict
        self.exclude_window = exclude_window   
   
        
    def filter_torque(self) -> None:
        """Apply the exclusion window to the torque signal."""
        self.torque = self.torque * self.exclude_window
    
    
    def plot_angle(self) -> None:
        """Plot the angle signal."""
        plt.figure(figsize=(12, 3))
        plt.plot(self.time, self.angle, label="Angle", color="C3")
        plt.xlabel("Time (UTC)" if self.over_UTC else "Sample index (k)")
        plt.ylabel("Angle")
        plt.grid(True)
        plt.legend(loc="upper left")
        plt.tight_layout()
        plt.show()

    def plot_torque(self) -> None:
        """Plot the torque signals (filtered and raw)."""
        plt.figure(figsize=(12, 3))
        plt.plot(
            self.time,
            self.torque,
            "C0",
            label="Filtered Torque"
        )
        plt.plot(
            self.time,
            self.torque_raw,
            "C5",
            lw=0.5,
            label="Raw Torque"
        )
        plt.xlabel("Time (UTC)" if self.over_UTC else "Sample index (k)")
        plt.ylabel("Torque (Nm)")
        plt.grid(True)
        plt.legend(loc="upper left")
        plt.tight_layout()
        plt.show()

    def plot_speed(self) -> None:
        """Plot the speed signal."""
        plt.figure(figsize=(12, 3))
        plt.plot(self.speed_window, label="Speed", color="C8")

        #plt.plot(self.time, self.speed_window, label="Speed", color="C8")
        plt.xlabel("Time (UTC)" if self.over_UTC else "Sample index (k)")
        plt.ylabel("Speed (°/s)")
        plt.grid(True)
        plt.legend(loc="upper left")
        plt.tight_layout()
        plt.show()