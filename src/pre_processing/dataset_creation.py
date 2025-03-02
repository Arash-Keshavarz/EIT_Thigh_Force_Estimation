import os
import glob
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from EIT_Thigh_Force_Estimation.src.pre_processing.pre_processing_utils import *
from scipy.signal import resample


def load_data(path):
    """Load EIT, JSON, and isometric force data from the given directory."""
    json_path = glob.glob(f"{path}/*.json")[0]
    eit_paths = glob.glob(f"{path}/eit_raw/**/*.npz", recursive=True)
    iso_csv_path = glob.glob(f"{path}/*.csv")[0]
    iso_py_path = f"{path}/iso_raw"
    
    with open(json_path, "r") as file:
        json_data = json.load(file)
    
    iso_raw_df = pd.read_csv(iso_csv_path)
    return eit_paths, json_data, iso_raw_df, iso_py_path

def process_isokinetic_force(iso_raw_df, iso_py_path, leg="right"):
    """Process Isokinetic force data from CSV and Python-based files."""
    iso_force_iso = IsoForceRAW(iso_raw_df, LP_filter_enabled=True, Leg=leg)
    iso_force_py = IsoForcePy(iso_py_path, Leg=leg, LP_filter_enabled=True, over_UTC=True, scale_0_1=True, distance=400)
    
    return iso_force_iso, iso_force_py, np.array([t.timestamp() for t in iso_force_py.time])

def process_json_information(json_data, torque_py_segments, torque_iso_segments):
    """Extract force levels and participant number from JSON data."""
    force_levels_str = json_data["isokinetic_measurement"]["force_levels"]
    participant_num = json_data["participant"]["Number"]

    force_levels = list(map(int, force_levels_str.strip("[]").split()))
    
    if set(torque_py_segments.keys()) != set(torque_iso_segments.keys()):
        print(f" Target Level: {force_levels[0]} was removed")
        force_levels.pop(0)

    return force_levels, participant_num

def process_torque_segments(torque_iso_segments, torque_py_segments):
    """Process and align torque segments from ISO and PY sources."""
    def extract_number(key):
        return int(key.split("_")[-1])
    
    if set(torque_py_segments.keys()) != set(torque_iso_segments.keys()):
        iso_keys_sorted = sorted(torque_iso_segments.keys(), key=extract_number)
        py_keys_sorted = sorted(torque_py_segments.keys(), key=extract_number)
        iso_values = [torque_iso_segments[k] for k in iso_keys_sorted]
        py_values = [torque_py_segments[k] for k in py_keys_sorted]
        min_length = min(len(iso_values), len(py_values))
        iso_values = iso_values[:min_length]
        py_values = py_values[:min_length]
        
        torque_iso_segments = {f"T_seg_{i}": iso_values[i] for i in range(min_length)}
        torque_py_segments = {f"T_seg_{i}": py_values[i] for i in range(min_length)}
    
    Iso_segments = []
    for idx, key in enumerate(torque_iso_segments.keys()):
        orig_min = np.min(torque_iso_segments[key])
        orig_max = np.max(torque_iso_segments[key])
        iso_seg = scale_to_range(torque_iso_segments[key])
        py_seg = scale_to_range(torque_py_segments[key])
        iso_seg_corr, py_seg_corr = resample_signals(iso_seg, py_seg)
        shift = detect_shift(iso_seg_corr, py_seg_corr)
        iso_seg, py_seg = resample_signals(iso_seg[shift:], py_seg, target_length=1500)
        Iso_segments.append(iso_seg * (orig_max - orig_min) + orig_min)
        plt.figure(figsize=(6, 3))
        plt.title(f"Correlation: {np.correlate(iso_seg, py_seg)[0] / len(iso_seg):.3f}")
        plt.plot(iso_seg, "C7", label="iso")
        plt.plot(py_seg, "C9", label="py")
        plt.legend()
        plt.show()
    return Iso_segments

def save_eit_samples(eit_pth, isoforce_py, isoforce_unix_time, isoforce_iso, force_levels, participant_num, dataset_path="./Dataset_test1"):
    """Extract and save EIT samples with corresponding torque data."""
    os.makedirs(dataset_path, exist_ok=True)
    existing_files = [f for f in os.listdir(dataset_path) if f.startswith("sample") and f.endswith(".npz")]
    if existing_files:
        existing_files.sort()
        last_file = existing_files[-1]  # Get the last created sample file
        last_index = int(last_file[6:11])  # Extract the numeric part from "sampleXXXXX.npz"
        sample_counter = last_index + 1  # Continue from the last index
    else:
        sample_counter = 0  # Start from 0 if no files exist
    
    eit_data, eit_timestamps = [], []
    for ele in np.sort(eit_pth):
        tmp = np.load(ele, allow_pickle=True)
        eit_data.append(tmp['eit']) 
        eit_timestamps.append(tmp['timestamp'])
    
    eit_data = np.array(eit_data)
    eit_data_abs = np.abs(eit_data) 
    eit_timestamps = np.array(eit_timestamps)
    
    for i, (start, stop) in enumerate(zip(isoforce_py.start_idxs, isoforce_py.stop_idxs)):
        
        start_time = isoforce_unix_time[start]
        stop_time = isoforce_unix_time[stop]
        
        start_idx = np.argmin(np.abs(eit_timestamps - start_time))
        stop_idx = np.argmin(np.abs(eit_timestamps - stop_time))
        
        eit_segment = eit_data_abs[start_idx:stop_idx+1, :, :]
        
        torque_segment = isoforce_iso.torque_segments[f"T_seg_{i}"]
        torque_resampled = resample(torque_segment, len(eit_segment))
        target_force = force_levels[i]
        
        for j, (eit_frame, torque_value) in enumerate(zip(eit_segment, torque_resampled)):
            filename = os.path.join(dataset_path, f"sample{sample_counter:05d}.npz")
            timestamp = eit_timestamps[start_idx + j]
            np.savez(filename,
                     eit=eit_frame,
                     torque=torque_value,
                     timestmps=timestamp, 
                     target_force=target_force, 
                     participant=participant_num)
            sample_counter += 1
    
    print(f"Saved {sample_counter} samples successfully!")
