"""
eit_module.py

This module provides a GUI for configuring and performing an EIT measurement.
It uses customtkinter for the UI, and integrates with an EIT measurement system using Sciopy package.
"""

import os
import time
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from sciopy import EIT_16_32_64_128, EitMeasurementSetup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration constants
FONT_TITLE = ("Arial", 20, "bold")
FONT_LABEL = ("Arial", 14)
COLOR_TEXT = "#3a3a3a"
COLOR_FRAME = "#e0e0e0"
COLOR_ENTRY_BG = "#f0f0f0"
COLOR_BORDER = "#3a3a3a"
COLOR_BUTTON = "#6c757d"
COLOR_BUTTON_HOVER = "#5a6268"
COLOR_START = "#1F6F2b"
COLOR_START_HOVER = "#166424"
COLOR_STOP = "#dc3545"
COLOR_STOP_HOVER = "#ff4d4d"

class EITMeasurementModule:
    
    """
    A module to configure and perform EIT measurements.
    """
    def __init__(self, parent: ctk.CTk) -> None:
        """
        Initialize the EIT measurement module with UI components.

        Args:
            parent (ctk.CTk): The parent container for the module.
        """

        self.frame = ctk.CTkFrame(parent, corner_radius=15, fg_color=COLOR_FRAME)
        self.frame.grid(row=0, column=0, padx=20, pady=20)
        self.frame.grid_columnconfigure(0, weight=0)  # Label column
        self.frame.grid_columnconfigure(1, weight=1)  # Entry column
        
        # Title Label
        title_label = ctk.CTkLabel(
            self.frame,
            text="EIT Measurement Config",
            font=FONT_TITLE,
            text_color=COLOR_TEXT
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=20)

        # Parameter Inputs
        self.entries: Dict[str, ctk.CTkEntry] = {}
        self.create_parameter_inputs()
        
        # Notes Area
        self.note_entry = ctk.CTkTextbox(self.frame, width=400, height=100, corner_radius=5)
        self.note_entry.insert("0.0", "Notes during the experiment")
        self.note_entry.bind("<FocusIn>", lambda e: self.clear_placeholder())
        self.note_entry.grid(
            row=len(self.entries) + 1,
            column=0,
            columnspan=2,
            padx=10,
            pady=10,
            sticky="nsew"
        )

        # Start Button
        self.start_button = ctk.CTkButton(
            self.frame,
            text="Start EIT Measurement",
            fg_color=COLOR_START,
            hover_color=COLOR_START_HOVER,
            command=self.start_measurement
        )
        self.start_button.grid(row=len(self.entries) + 2, column=0, columnspan=2, sticky="n")

        # Optional: Create a frame for plotting results if needed.
        # self.plot_frame = ctk.CTkFrame(self.frame)
        # self.plot_frame.grid(row=len(self.entries) + 3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

    def clear_placeholder(self) -> None:
        """
        Clear the placeholder text in the notes textbox if it matches the default.
        """
        current_text = self.note_entry.get("0.0", "end").strip()
        if current_text == "Notes during the experiment":
            self.note_entry.delete("0.0", "end")

    def create_parameter_inputs(self) -> None:
        """
        Create input fields for various measurement parameters.
        """
        params: Dict[str, str] = {
            "Excitation Frequency (Hz)": "125_000",
            "Burst Count": "0",
            "Amplitude (mA)": "0.01",
            "Frame Rate (fps)": "3",
            "Injection Skip": "5",
            "Force Level": "[20-80]"
        }
        for i, (label_text, default_value) in enumerate(params.items()):
            lbl = ctk.CTkLabel(
                self.frame,
                text = label_text,
                font = FONT_LABEL,
                text_color = COLOR_TEXT
            )
            lbl.grid(row=i + 1, column=0, padx=10, pady=(10, 5), sticky="w")
            entry = ctk.CTkEntry(
                self.frame,
                width = 150,
                placeholder_text=default_value,
                border_color=COLOR_BORDER,
                fg_color=COLOR_ENTRY_BG
            )
            entry.configure(text_color=COLOR_TEXT)
            entry.grid(row=i + 1, column=1, padx=10, pady=(10, 5), sticky="w")
            self.entries[label_text] = entry
            
    def start_measurement(self) -> None:
        """
        Extract parameters, perform the measurement, and display a success or error message.
        """
        try:
            # Convert entry values to float when possible; leave as string otherwise.
            params = {
                key: float(entry.get()) if entry.get().replace('.', '', 1).isdigit() else entry.get()
                for key, entry in self.entries.items()
            }
            logging.info("Starting EIT measurement with parameters: %s", params)
            data = self.perform_measurement(params)
            CTkMessagebox(
                title="Success",
                message="Measurement complete.",
                icon="check",
                option_1="OK"
            )
            
            # Optionally, plot the results if data and a plot frame are available:
            # if data is not None:
            #     self.plot_results(data)
            
        except Exception as e:
            logging.error("Error during measurement: %s", e)
            CTkMessagebox(title="Error", message=f"Error: {e}", icon="cancel")
            
    def perform_measurement(
        self, params: Dict[str, Any], save_dir: str = 'measurement_EITpy'
    ) -> Optional[np.ndarray]:
        """
        Perform the EIT measurement and save the data.

        Args:
            params (Dict[str, Any]): Dictionary of measurement parameters.
            save_dir (str): Directory where the measurement data will be saved.

        Returns:
            Optional[np.ndarray]: The measurement data, or None if measurement failed.
        """
        os.makedirs(save_dir, exist_ok=True)
        eit_dir = os.path.join(save_dir, "eit_py")
        os.makedirs(eit_dir, exist_ok=True)

        # Determine the next available filename
        files = [
            f for f in os.listdir(eit_dir)
            if f.startswith("sample_") and f.endswith(".npz")
        ]
        max_index = max((int(f.split("_")[1].split(".")[0]) for f in files), default=-1)
        next_index = max_index + 1
        save_path = os.path.join(eit_dir, f"sample_{next_index:05d}.npz")

        try:
            n_el = 16
            sciospec = EIT_16_32_64_128(n_el)
            sciospec.connect_device_HS()
            sciospec.SystemMessageCallback()

            setup = EitMeasurementSetup(
                burst_count=int(params["Burst Count"]),
                n_el=n_el,
                exc_freq=float(params["Excitation Frequency (Hz)"]),
                framerate=int(params["Frame Rate (fps)"]),
                amplitude=float(params["Amplitude (mA)"]),
                inj_skip=n_el // 2,  # Using calculated injection skip
                gain=1,
                adc_range=1,
            )
            sciospec.SetMeasurementSetup(setup)

            start_timestamp = time.time()
            logging.info("EIT measurement started at %s", datetime.fromtimestamp(start_timestamp))
            data = sciospec.StartStopMeasurement(return_as="pot_mat")
            end_timestamp = time.time()
            logging.info("EIT measurement ended at %s", datetime.fromtimestamp(end_timestamp))

            np.savez(
                save_path,
                data=data,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                force_level=params["Force Level"]
            )
            logging.info("Measurement data saved to %s", save_path)

            return data
        except Exception as e:
            logging.error("Error during EIT measurement: %s", e)
            CTkMessagebox(title="Error", message=f"Measurement failed: {e}", icon="cancel")
            return None
            
    def plot_results(self, data: np.ndarray) -> None:
        """
        Plot the EIT measurement results.

        Args:
            data (np.ndarray): The measurement data to plot.
        """
        # Check if plot_frame exists; if not, display an error.
        if not hasattr(self, 'plot_frame'):
            logging.error("Plot frame not defined. Cannot plot results.")
            CTkMessagebox(title="Plot Error", message="Plot frame not defined.", icon="cancel")
            return

        # Clear previous plots
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(3, 3))
        ax.imshow(np.abs(data[0]), cmap="viridis")
        ax.set_title("EIT Measurement Results")

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


    def get_parameters(self, parameter_name: str) -> str:
        """
        Retrieve the value of a specified parameter.

        Args:
            parameter_name (str): The name of the parameter.

        Returns:
            str: The value of the parameter.
        """
        if parameter_name in self.entries:
            return self.entries[parameter_name].get()
        else:
            raise ValueError(f"Parameter '{parameter_name}' not found.")

    def get_note_entry_text(self) -> str:
        """
        Retrieve the text from the notes textbox.

        Returns:
            str: The notes text.
        """
        return self.note_entry.get("0.0", "end").strip()