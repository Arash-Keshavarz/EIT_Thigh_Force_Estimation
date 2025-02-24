from dataclasses import dataclass
from glob import glob
from os.path import join
from typing import Union
import matplotlib.pyplot as plt
import os
import json

import numpy as np


@dataclass
class Participant:
    Number: str
    age: str
    gender: str
    leg: str


@dataclass
class IsokinetikMeasurement:
    rotation_velocity: str
    force_levels: np.ndarray


@dataclass
class EITmeasurement:
    excitation_frequency: Union[int, float]
    burst_count: int
    amplitude: Union[int, float]
    frame_rate: int
    n_el: int
    injection_skip: int


class Protocol:
    def __init__(self, path: str, prints: bool = True):
        self.path = path
        self.prints = prints

        self.read_json()

    def read_json(self):
        self.json_path = glob(join(self.path, "*protocol.json"))[0]
        with open(self.json_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if self.prints:
            print(self.json_path)
            print(data)

        # Participant
        self.Participant = Participant(**data["participant"])

        # IsokinetikMeasurement
        rotation_velocity = int(
            data["isokinetic_measurement"]["rotation_velocity"].split(" ")[0]
        )
        force_levels = data["isokinetic_measurement"]["force_levels"]
        force_levels = np.array(
            list(map(int, force_levels.strip("[]").split())), dtype=int
        )
        self.IsokinetikMeasurement = IsokinetikMeasurement(
            rotation_velocity, force_levels
        )
        # EITmeasurement
        excitation_frequency = data["eit_measurement"]["excitation_frequency"]
        burst_count = data["eit_measurement"]["burst_count"]
        amplitude = int(data["eit_measurement"]["amplitude"].split(" ")[0])
        frame_rate = data["eit_measurement"]["frame_rate"]
        n_el = data["eit_measurement"]["n_el"]
        injection_skip = data["eit_measurement"]["injection_skip"]

        self.EITmeasurement = EITmeasurement(
            excitation_frequency,
            burst_count,
            amplitude,
            frame_rate,
            n_el,
            injection_skip,
        )

        # Notes
        self.notes = data["notes"]
