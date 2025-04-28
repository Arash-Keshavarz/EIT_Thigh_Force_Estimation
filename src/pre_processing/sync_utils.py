import os
import logging
from typing import Dict, List, Tuple

import numpy as np
from glob import glob
from tqdm import tqdm
from dtaidistance import dtw
import matplotlib.pyplot as plt

from toolbox import Protocol
from pre_processing.pre_processing_utils import IsoForceRAW, IsoForcePy
from pre_processing.eit_utils import load_eit_npz

logger = logging.getLogger(__name__)


def find_nearest_index(array: np.ndarray, value: float) -> int:
    """
    Return the index of the closest element in 'array' to 'value'.
    """
    idx = int(np.argmin(np.abs(array - value)))
    logger.debug("Nearest index to %f is %d", value, idx)
    return idx


def find_best_dtw_match(
    long_series: np.ndarray,
    reference_series: np.ndarray,
    window_size: int = 4
) -> Tuple[int, float]:
    """
    Slide a window of size 'window_size' over 'long_series' to find the segment
    minimizing DTW distance to 'reference_series'.

    Returns (best_start_index, best_distance).
    """
    best_idx = 0
    best_dist = float('inf')
    for i in range(len(long_series) - window_size + 1):
        segment = long_series[i:i+window_size]
        dist = dtw.distance(reference_series, segment)
        if dist < best_dist:
            best_dist = dist
            best_idx = i
    logger.info("Best DTW match at %d (distance=%.3f)", best_idx, best_dist)
    return best_idx, best_dist


def sync_NI_PY_times(
    isoforce_iso: IsoForceRAW,
    isoforce_py: IsoForcePy,
    seg_idx: int = 0,
    plotting: bool = False
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Align torque segments from IsoForceRAW and IsoForcePy by matching lengths.

    Returns (timestamps_iso, sampled_iso_torque).
    """
    raw_seg = isoforce_iso.torque_segments[f"T_seg_{seg_idx}"]
    py_seg = isoforce_py.torque_segments[f"T_seg_{seg_idx}"]
    ts_seg = isoforce_py.timestamps_segments[f"TS_seg_{seg_idx}"]

    if len(py_seg) != len(ts_seg):
        logger.error("Length mismatch: py_seg (%d) vs ts_seg (%d)", len(py_seg), len(ts_seg))
        raise ValueError("IsoForcePY segments and timestamps length mismatch")

    # uniformly sample raw segment to match Python timestamps
    indices = np.linspace(0, len(raw_seg) - 1, len(ts_seg), dtype=int)
    sampled_raw = raw_seg[indices]

    if plotting:
        plt.figure(figsize=(6, 2))
        plt.title(f"Segment {seg_idx} alignment")
        plt.plot(raw_seg, label="Raw IsoForce")
        plt.plot(indices, py_seg * 60, '--', label="Python IsoForce")
        plt.scatter(indices, sampled_raw, c='red', marker='x', label="Sampled")
        plt.ylabel("Torque (Nm)")
        plt.xlabel("Sample index")
        plt.legend()
        plt.grid(True)
        plt.show()

    return ts_seg, sampled_raw


def synchronize_eit_force_data(
    eit_path: str,
    isoforce_iso: IsoForceRAW,
    isoforce_py: IsoForcePy,
    mode: str = "fast",
    export_dir: str = None
) -> Dict[str, np.ndarray]:
    """
    Synchronize EIT frames with isokinetic torque measurements.

    Args:
        eit_path: Path to EIT .npz folder.
        isoforce_iso: Raw IsoForce data object.
        isoforce_py: Processed IsoForce data object.
        mode: 'fast' uses nearest-timestamp; 'slow' uses DTW on initial window.
        export_dir: If provided, save each synced sample as .npz files.

    Returns:
        Dict with keys 'eit', 'torque', 'ts_iso', 'ts_eit' containing concatenated arrays.
    """
    protocol = Protocol(eit_path, verbose=False)
    force_levels = protocol.IsokineticMeasurement.force_levels

    # load EIT data
    eit_timestamps, eit_data = load_eit_npz(eit_path)

    all_eit = []
    all_torque = []
    all_ts_iso = []
    all_ts_eit = []
    sample_counter = 0

    for idx in range(len(isoforce_iso.torque_segments)):
        ts_seg, sampled = sync_NI_PY_times(isoforce_iso, isoforce_py, idx, plotting=True)

        if mode == "fast":
            sync_idx = [find_nearest_index(eit_timestamps, t) for t in ts_seg]
        else:
            start, _ = find_best_dtw_match(eit_timestamps, ts_seg[:5])
            sync_idx = list(range(start, start + len(ts_seg)))

        # time-diff checks
        dt_start = ts_seg[0] - eit_timestamps[sync_idx[0]]
        dt_end = ts_seg[-1] - eit_timestamps[sync_idx[-1]]
        if abs(dt_start) > 5 or abs(dt_end) > 5:
            logger.warning("Skipping segment %d: time mismatch [%.2f, %.2f]", idx, dt_start, dt_end)
            continue

        segment_eit = eit_data[sync_idx]
        segment_torque = sampled
        segment_ts_eit = eit_timestamps[sync_idx]

        all_eit.append(segment_eit)
        all_torque.append(segment_torque)
        all_ts_iso.append(ts_seg)
        all_ts_eit.append(segment_ts_eit)

        if export_dir:
            os.makedirs(export_dir, exist_ok=True)
            for i, (e, tq, t_iso, t_eit) in enumerate(zip(segment_eit, sampled, ts_seg, segment_ts_eit)):
                filename = os.path.join(export_dir, f"sample_{sample_counter:05d}.npz")
                np.savez(
                    filename,
                    eit=e,
                    torque=tq,
                    ts_iso=t_iso,
                    ts_eit=t_eit,
                    target_force=force_levels[idx],
                    participant=protocol.Participant.Number
                )
                sample_counter += 1

    result = {
        'eit': np.concatenate(all_eit),
        'torque': np.concatenate(all_torque),
        'ts_iso': np.concatenate(all_ts_iso),
        'ts_eit': np.concatenate(all_ts_eit),
    }
    return result
