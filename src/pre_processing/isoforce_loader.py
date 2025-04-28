import os
import logging
from glob import glob
from typing import Tuple

import pandas as pd

from toolbox import Protocol
from pre_processing.pre_processing_utils import IsoForceRAW, IsoForcePy

logger = logging.getLogger(__name__)


def process_isoforce_data(
    data_path: str,
    segment_length_threshold: int,
    distance: float,
    plot: bool = False
) -> Tuple[IsoForceRAW, IsoForcePy]:
    """
    Load and preprocess IsoForce measurement data.

    Args:
        data_path: Directory containing CSV measurement file.
        segment_length_threshold: Minimum length (in samples) of valid segments.
        distance: Peak-detection distance threshold.
        plot: If True, show raw and processed torque plots.

    Returns:
        iso_force_raw: IsoForceRAW instance with raw data.
        iso_force_py: IsoForcePy instance with Python-processed data.
    """
    # Locate CSV file
    csv_files = glob(os.path.join(data_path, "*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV file found in {data_path}")
    iso_csv = csv_files[0]
    logger.info(f"Loading IsoForce CSV: %s", iso_csv)

    # Build protocol
    protocol = Protocol(data_path, verbose=False)
    logger.debug("Protocol loaded: %s", protocol)

    # Read raw CSV into dataframe
    df_raw = pd.read_csv(iso_csv)
    iso_force_raw = IsoForceRAW(
        df_raw,
        LP_filter_enabled=True,
        Protocol=protocol
    )

    # Initialize Python-processed object
    iso_force_py = IsoForcePy(
        data_path,
        Protocol=protocol,
        LP_filter_enabled=True,
        over_UTC=False,
        scale_0_1=True,
        segment_len_threshold=segment_length_threshold,
        distance=distance,
    )

    if plot:
        logger.info("Plotting torque curves for raw and processed data")
        iso_force_raw.plot_torque()
        iso_force_py.plot_torque()

    return iso_force_raw, iso_force_py
