from dataclasses import dataclass
from glob import glob
from os.path import join
from typing import Union
import json
import numpy as np

@dataclass
class Participant:
    Number: str
    age: str
    gender: str
    leg: str
    
@dataclass
class IsokineticMeasurement:
    rotation_velocity: int
    force_levels: np.ndarray


@dataclass
class EITMeasurement:
    excitation_frequency: Union[int, float]
    burst_count: int
    amplitude: Union[int, float]
    frame_rate: int
    n_el: int
    injection_skip: int
    
    
class Protocol:
    """Handles reading and parsing protocol JSON files for experiments."""

    def __init__(self, path: str, verbose: bool = True):
        """
        Initializes the Protocol class.

        :param path: Directory containing the protocol JSON file.
        :param verbose: If True, prints loaded data for debugging.
        """
        self.path = path
        self.verbose = verbose
        self.json_path = None
        self.Participant = None
        self.IsokineticMeasurement = None
        self.EITMeasurement = None
        self.notes = ""

        self.read_json()

    def read_json(self):
        """Reads and parses the protocol JSON file."""
        try:
            json_files = glob(join(self.path, "*protocol.json"))
            if not json_files:
                raise FileNotFoundError("No protocol JSON file found in the given path.")
            self.json_path = json_files[0]

            with open(self.json_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if self.verbose:
                print(f"Loaded protocol file: {self.json_path}")

            # Parse Participant
            self.Participant = Participant(**data.get("participant", {}))

            # Parse Isokinetic Measurement
            iso_data = data.get("isokinetic_measurement", {})
            rotation_velocity = self._extract_int(iso_data.get("rotation_velocity"))
            force_levels = self._parse_force_levels(iso_data.get("force_levels"))
            self.IsokineticMeasurement = IsokineticMeasurement(rotation_velocity, force_levels)

            # Parse EIT Measurement
            eit_data = data.get("eit_measurement", {})
            self.EITMeasurement = EITMeasurement(
                excitation_frequency=eit_data.get("excitation_frequency", 0),
                burst_count=eit_data.get("burst_count", 0),
                amplitude=self._extract_int(eit_data.get("amplitude")),
                frame_rate=eit_data.get("frame_rate", 0),
                n_el=eit_data.get("n_el", 0),
                injection_skip=eit_data.get("injection_skip", 0),
            )

            # Parse Notes
            self.notes = data.get("notes", "")

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading protocol JSON: {e}")

    @staticmethod
    def _extract_int(value: str) -> int:
        """Extracts integer from a string containing a number and unit (e.g., '30 deg/s')."""
        if isinstance(value, str):
            return int(value.split()[0])
        return int(value) if value is not None else 0

    @staticmethod
    def _parse_force_levels(force_levels: str) -> np.ndarray:
        """Parses a force level string into a NumPy array."""
        if isinstance(force_levels, str):
            try:
                return np.array([int(x) for x in force_levels.strip("[]").split()], dtype=int)
            except ValueError:
                return np.array([])
        return np.array(force_levels, dtype=int) if force_levels else np.array([])