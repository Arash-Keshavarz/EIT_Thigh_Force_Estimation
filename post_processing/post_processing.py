import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
from scipy.signal import butter, filtfilt, find_peaks
import re
from datetime import datetime, timedelta, timezone


def lowpass_filter(data, cutoff=2, fs=100, order=4):
    """ Applying the low pass(LP) filter

    Args:
        data (_type_): input signal
        cutoff (int, optional):the cut off frequency. Defaults to 2.
        fs (int, optional): the sampling rate. Defaults to 100.
        order (int, optional): the order of filter. Defaults to 4.

    """
    
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    filtered_signal = filtfilt(b, a, data)
    return filtered_signal


def scale_to_range(values, new_min=0, new_max=1):
    """Scales input value(s) from their original range to a new specified range [new_min, new_max].

    Args:
        values (float, list, or tuple): Input value(s) to scale. Can be a single number, list, or tuple.
        new_min (float): The lower bound of the new range (default is 0).
        new_max (float): The upper bound of the new range (default is 1).
    

    Returns:
        float, list, or tuple: Scaled value(s) within the specified range. The return type matches the input type.
    """
    
    old_min = np.min(values)
    old_max = np.max(values)

    def scale(value):
        return new_min + (value - old_min) * (new_max - new_min) / (old_max - old_min)

    if isinstance(values, (list, tuple)):
        return type(values)(scale(value) for value in values)
    else:
        return scale(values)
    
def edge_detection(signal, mode="rising", threshold=1):
    """
    Detects edges (rising or falling) in a signal based on a specified threshold.

    Parameters:
        signal (array-like): The input signal,
        mode (str): The type of edge to detect. 
                    - "rising": Detects rising edges where the signal difference equals the threshold.
                    - "falling": Detects falling edges where the signal difference equals the negative threshold.
                    Default is "rising".
        threshold (int or float): The difference value that defines an edge. Default is 1.

    Returns:
        numpy.ndarray: The indices of the detected edges in the signal.

    """
    
    signal = np.asarray(signal)
    diff = np.diff(signal)
    if mode == "rising":
        rising_edges = np.where(diff == threshold)[0]
    elif mode == "falling":
        rising_edges = np.where(diff == -threshold)[0]
    return rising_edges

def convert_timestamp(date_str):
    if len(str(date_str).split(".")) > 2:
        timestamp = datetime.strptime(date_str, "%Y.%m.%d. %H:%M:%S.%f")
        return timestamp.timestamp()
    else:
        date_time = datetime.fromtimestamp(float(date_str))
        return date_time.strftime("%Y.%m.%d. %H:%M:%S.%f")
    
def generate_DF(file_path, output_path):
    
    """   Converts raw ISO data from a .txt file into a cleaned DataFrame and saves it as a .csv file.


    Args:
        file_path (str): The path to the input .txt file containing raw ISO data.
        output_path (str): The path to save the cleaned data as a .csv file.

    Returns:
        pandas.DataFrame: A cleaned DataFrame containing the following columns:
            - "Torque": Numeric values from the torque column.
            - "Angle": Numeric values from the angle column.
            - "Velocity": Numeric values from the velocity column.
    """
    
    iso_data = pd.read_csv(file_path, delimiter="\t", header=0)

    #extract the first column (Torque)
    torque_column = iso_data["Torque (or Velocity - ISOT, or Force - CKC)"]
    torque_column = torque_column.str.replace(',', '.', regex=False)
    torque_column_cleaned = pd.to_numeric(torque_column, errors='coerce').dropna()

    #extract the second column (Angle)
    angle_column = iso_data["Angle (or Distance - CKC)"]
    angle_column = angle_column.str.replace(',', '.', regex=False)
    angle_column_cleaned = pd.to_numeric(angle_column, errors='coerce').dropna()

    #extract the third column (Velocity)
    speed_column = iso_data["Velocity (or Torque - ISOT, or Force - CKC)"]
    speed_column = speed_column.str.replace(',', '.', regex=False)
    speed_column_cleaned = pd.to_numeric(speed_column, errors='coerce').dropna()
    
    iso_raw_df = pd.DataFrame({
        "Torque": torque_column_cleaned,
        "Angle": angle_column_cleaned,
        "Velocity": speed_column_cleaned
    })

    # saved the cleaned data
    iso_raw_df.to_csv(output_path, index=False)

    print(f"cleaned data saved to {output_path}")

    return iso_raw_df


class IsoForceRAW:

    """
        Post process the Isoforcekinetic data from Original device
    """

    def __init__(self, DF, LP_filter=False):

        self.DF = DF
        self.LP_filter = LP_filter

        self.init_data()
        self.detect_start_stop_idxs()
        self.export_segments()
        self.filter_torque()

    def init_data(self):
        
        # getting raw data from iso-device
        self.torque_raw = self.DF["Torque"]
        self.angle_raw = self.DF["Angle"]
        self.speed = self.DF["Velocity"]

        if self.LP_filter:
            print("The torque and angle data are LP-filtered !")
            self.torque = lowpass_filter(self.torque_raw)
            self.angle = lowpass_filter(self.angle_raw)
        else:
            self.torque = self.torque_raw
            self.angle = self.angle_raw
       

    def detect_start_stop_idxs(self):

        # use the speed edges for start and stop times
        k = np.arange(len(self.speed))
        dx_dk = np.gradient(self.speed, k)
        self.start_idxs = np.where(dx_dk > np.mean(dx_dk))[0][1::2]
        self.stop_idxs = np.where(dx_dk < -np.mean(dx_dk))[0][::2]
        # length quality check
        too_short = np.where(self.stop_idxs - self.start_idxs < 1000)[0]  # exclude if the segment is too short lower threshold 1000
        too_long = np.where(self.stop_idxs - self.start_idxs > 2500)[0]   # exclude if the segment is too long  upper threshold 2500
        cut_out = np.concatenate([too_short, too_long])
        self.stop_idxs = np.delete(self.stop_idxs, cut_out)
        self.start_idxs = np.delete(self.start_idxs, cut_out)


    def export_segments(self):
        idx = 0
        T_segment_dict = dict()
        A_segment_dict = dict()
        exclude_window = np.zeros(len(self.speed))
        for start, stop in zip(self.start_idxs, self.stop_idxs):
            T_segment_dict[f"T_seg_{idx}"] = self.torque[start:stop]
            A_segment_dict[f"A_seg_{idx}"] = self.angle[start:stop]

            exclude_window[start:stop] = 1
            idx += 1

        self.exclude_window = exclude_window
        self.torque_segments = T_segment_dict
        self.angle_segments = A_segment_dict

    def filter_torque(self):
        self.torque_seg = self.torque * self.exclude_window

    def plot_torque(self):
        """T -> Torque"""
        tks = np.round(np.linspace(np.min(self.torque), np.max(self.torque), 5))

        plt.figure(figsize=(12, 3))
        plt.plot(self.torque_seg, "C0", label=".torque")
        plt.plot(self.torque, "C8", lw=0.5, label=".torque_raw")
        plt.grid()
        plt.legend()
        plt.xlabel("sample $k$")
        plt.ylabel("Torque (NM)")
        plt.show()

    def plot_angle(self):
        """P -> angle"""
        plt.figure(figsize=(12, 3))
        plt.plot(self.angle, "C3")
        plt.grid()
        plt.xlabel("sample $k$")
        plt.ylabel("Angle (°)")
        plt.show()

    def plot_speed(self):
        plt.figure(figsize=(12, 3))
        plt.plot(self.speed, "C8")
        plt.scatter(
            self.start_idxs, self.speed[self.start_idxs], c="C2", label="start idx"
        )
        plt.scatter(
            self.stop_idxs, self.speed[self.stop_idxs], c="C3", label="stop idxs"
        )
        plt.grid()
        plt.xlabel("sample $k$")
        plt.ylabel("Speed (°/s)")
        plt.legend(loc="upper left")
        plt.show()

    def plot_data(self, filename=None):

        plt.figure(figsize=(12, 3))
        plt.plot(self.torque_seg,"C0", label="Torque")
        plt.plot(self.angle,"C3", label="Angle")
        plt.plot(self.speed,"C8", label="Speed")
        plt.scatter(
            self.start_idxs, self.speed[self.start_idxs], c="C2", label="start idx"
        )
        plt.scatter(
            self.stop_idxs, self.speed[self.stop_idxs], c="C4", label="stop idxs"
        )
        plt.legend(loc="upper left")
        plt.grid()
        plt.xlabel("sample $k$")
        if filename != None:
            plt.tight_layout()
            plt.savefig(filename)
        plt.show()

###############################
# Class for processing IsoData from NI chip


def extract_timestamp_and_sample(filename):
    """
        extract timestamp and sample number from filename
    """
    match = re.search(r"_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_(\d+)\.npz$", filename)

    if match:
        timestamp_str = match.group(1)  # Extract the timestamp
        sample_number = int(match.group(2))  # Extract the sample number
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")  # Convert to datetime

        return timestamp, sample_number
    return None, None



class IsoForcePy:
    """The class for processing the IsoForce data acquired from the Python script.
    """
    def __init__(self, path, LP_filter=True, over_UTC=False, scale_0_1=True, speed_window_trunc=True, phase_shift=0):
        
        """
        path ... part_path.isoforce_py_raw.
        LP_filter ... low-pass filter the torque data.
        over_UTC ... plot over the measured time stamps.
        scale_0_1 ... scale all analog measured values between 0 and 1.
        speed_window_trunc ... create a speed window.
        phase_shift ... time index phase shift between Isoforce and Python (heuristic).
        """

        self.path = path
        self.LP_filter = LP_filter
        self.over_UTC = over_UTC
        self.scale_0_1 = scale_0_1
        self.speed_window_trunc = speed_window_trunc
        self.phase_shift = phase_shift
        
        self.init_data()
        self.export_segments()
        self.filter_torque()

    def init_data(self):
        # initilize lists to store aggregated data
        angle = [] # ch1
        torque = [] # ch2
        speed = []  #ch3
        time = [] #timestamps
        time_UNIX = []

        file_list = sorted(
            [f for f in os.listdir(self.path) if f.endswith(".npz")],
            key=lambda f: (extract_timestamp_and_sample(f)),)
        
         
        last_file_for_timestamp = dict()

        for file_name in file_list:
            timestamp, sample_number = extract_timestamp_and_sample(file_name)
            last_file_for_timestamp[timestamp] = (
                file_name  # Overwrite with the latest file
            )

        for timestamp, last_file in last_file_for_timestamp.items():
            file_path = os.path.join(self.path, last_file)
            data = np.load(file_path, allow_pickle=True)

            # Extract the data for the last file of this timestamp
            ch_1, ch_2, ch_3 = data["data"]
            assert len(ch_1) == len(ch_2) == len(ch_3)

            timestamps_start = data["timestamps_start"]
            timestamps = data["timestamps_current"]
            sampling_rate = data["sampling_rate"]

            # Expand timestamps for the last sample file
            timestamps_expanded = [
                timestamp + timedelta(seconds=(i / sampling_rate))
                for i in range(len(ch_1))
            ]

            # Append the torque and time data
            angle.extend(ch_1)
            torque.extend(ch_2)
            speed.extend(ch_3)
            time.extend(timestamps_expanded)
            #time_UNIX.extend(timestamps)

        #set class variables
        self.time_UNIX = np.array(time_UNIX)
        self.angle = np.array(angle)
        self.torque_raw = np.array(torque)
        if self.LP_filter:
            self.torque = lowpass_filter(self.torque_raw)
        else:
            self.torque = self.torque_raw
            
        self.speed = np.array(speed)

        if self.scale_0_1:
            self.angle = scale_to_range(self.angle)
            self.torque = scale_to_range(self.torque)
            self.torque_raw = scale_to_range(self.torque_raw)
            self.speed = scale_to_range(self.speed)
            
        if self.speed_window_trunc:
            speed_window = self.speed
            speed_window[self.speed <= 0.95] = 0
            speed_window[self.speed > 0.5] = 1 
            self.speed_window = speed_window           
            
        
        assert len(angle) == len(torque) == len(speed)

        if self.over_UTC:
            self.time = np.array(time)
        else:
            self.time = np.arange(len(time))
    def export_segments(self, distance = 500, height=0.8):
        idx = 0
        T_segment_dict = dict()
        A_segment_dict = dict()
        
        self.stop_idxs, _ = find_peaks(self.angle, distance=distance, height=height)
        
        start_detected = edge_detection(self.speed)
        
        start_filt = list()
        
        for stop in self.stop_idxs:
            
            diff = stop - start_detected
            min_diff = np.argmin(diff[diff > 0])
            start_filt.append(start_detected[min_diff])
            
        self.start_idxs = np.array(start_filt) - self.phase_shift
        
        # exlude all segments that are shorter than 300 samples (~3s)
        
        len_mask = self.stop_idxs - self.start_idxs > 300        # if fs = 100
        self.start_idxs = self.start_idxs[len_mask]
        self.stop_idxs = self.stop_idxs[len_mask]
        
        assert(
            self.start_idxs.shape == self.stop_idxs.shape) , "start_idxs and stop_idxs are not the same"
        
        exclude_window = np.zeros(len(self.torque))
        for start, stop in zip(self.start_idxs, self.stop_idxs):
            T_segment_dict[f"T_seg_{idx}"] = self.torque[start:stop]
            A_segment_dict[f"A_seg_{idx}"] = self.angle[start:stop]
            exclude_window[start:stop] = 1
            idx += 1
        
        self.torque_segments = T_segment_dict
        self.angle_segments = A_segment_dict
        self.exclude_window = exclude_window
        
    def filter_torque(self):
        self.torque = self.torque * self.exclude_window
    
    
    def plot_angle(self):
        
        plt.figure(figsize=(12, 3))
        if self.over_UTC:
            plt.plot(self.time, self.angle, label="Angle", color="C3")
            plt.xlabel("Time (UTC)")
        else:
            plt.plot(self.time, self.angle, label="Angle", color="C3")
            plt.xlabel("sample ($k$)")

        plt.ylabel("Angle")
        plt.grid(True)
        plt.legend(loc="upper left")
        plt.tight_layout()
        plt.show()
    
    def plot_torque(self):
        plt.figure(figsize=(12, 3))
        
        if self.over_UTC:
            plt.plot(self.time, self.torque, "C0", label=".torque")
            plt.plot(self.time, self.torque_raw, "C5", lw=0.5, label=".torque_raw")
            plt.xlabel("Time (UTC)")
        else:
            
            plt.plot(self.time, self.torque, "C0", label=".torque")
            plt.plot(self.time, self.torque_raw, "C5", lw=0.5, label=".torque_raw") 
            plt.xlabel("sample ($k$)")

        plt.ylabel("Torque (Nm)")
        plt.grid(True)
        plt.legend(loc="upper left")
        plt.tight_layout()
        plt.show()

    def plot_speed(self):
        plt.figure(figsize=(12, 3))
        if self.over_UTC:
            plt.plot(self.time, self.speed, label="Speed", color="C8")
            plt.xlabel("Time (UTC)")

        else:
            plt.plot(self.time, self.speed, label="Speed", color="C8")
            plt.xlabel("sample ($k$)")
            
        plt.ylabel("Speed (°/s)")
        plt.grid(True)
        plt.legend(loc="upper left")
        plt.tight_layout()
        plt.show()