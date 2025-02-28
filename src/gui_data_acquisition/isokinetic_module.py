"""
isokinetic_module.py

This module provides a GUI for configuring and controlling an isokinetic measurement.
It uses customtkinter for the UI and integrates with the NI DAQ system.
    
"""
import datetime
import json
import os
import threading
import time
from typing import Optional

import numpy as np
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from NI_module import ContinuousDAQ
from utils import create_participant_directory

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


class IsokineticMeasurementModule:
    
    """
    GUI Module for configuring and controlling isokinetic measurement.
    """
    
    def __init__(self, parent: ctk.CTk):
        """
         initialize the measurement module and create its UI components
        """
        
        self.frame = ctk.CTkFrame(parent, corner_radius=15, fg_color= COLOR_FRAME)
        self.frame.grid(row=0, column=0, padx=20, pady=20)
        self.frame.grid_columnconfigure(0, weight=0)  # Label column
        self.frame.grid_columnconfigure(1, weight=1)  # Entry column

        # NI DAQ and measurement attributes
        self.daq: Optional[ContinuousDAQ] = None
        self.acquisition_thread: Optional[threading.Thread] = None
        self.repeated_force_levels: Optional[np.ndarray] = None  # Force levels array
        self.tar_idx: int = 0
        self.raw_eit_dir: Optional[str] = None  # Store raw EIT directory if needed

        # Build UI components
        self.create_content()
        
        
    def create_content(self) -> None:
        """
        Create and layeout all UI components.    
        """
        # Title label
        title_label = ctk.CTkLabel(
            self.frame,
            text="Isokinetic Measurement Config",
            font=FONT_TITLE,
            text_color=COLOR_TEXT,
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Participant's Number
        self._create_labeled_entry(
            row=1,
            label_text="Participant's Number",
            placeholder="Enter number",
            attr_name="participant_number_entry",
        )
        
        # Participant's Age
        self._create_labeled_entry(
            row=2,
            label_text="Participant's Age",
            placeholder="Enter Age",
            attr_name="participant_age_entry",
        )
        
        # Participant's Gender
        gender_label = ctk.CTkLabel(
            self.frame, text="Participant's Gender", font=FONT_LABEL, text_color=COLOR_TEXT
        )
        gender_label.grid(row=3, column=0, padx=10, pady=(10, 5), sticky="w")

        self.participant_gender_box = ctk.CTkComboBox(
            self.frame,
            width=180,
            values=["male", "female"],
            border_color=COLOR_BORDER,
            fg_color=COLOR_ENTRY_BG,
            dropdown_fg_color=COLOR_ENTRY_BG,
            button_color=COLOR_BORDER,
            text_color=COLOR_TEXT,
            dropdown_text_color='#333333',
        )
        self.participant_gender_box.grid(row=3, column=1, padx=10, pady=(10, 5), sticky="w")
        
        # Participant's Leg
        leg_label = ctk.CTkLabel(
            self.frame, text="Participant's Leg", font=FONT_LABEL, text_color=COLOR_TEXT
        )
        leg_label.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="w")

        self.participant_leg_box = ctk.CTkComboBox(
            self.frame,
            width=180,
            values=["right", "left"],
            border_color=COLOR_BORDER,
            fg_color=COLOR_ENTRY_BG,
            dropdown_fg_color=COLOR_ENTRY_BG,
            button_color=COLOR_BORDER,
            text_color=COLOR_TEXT,
            dropdown_text_color='#333333',
        )
        self.participant_leg_box.grid(row=4, column=1, padx=10, pady=(10, 5), sticky="w")

        # Force Levels Button
        force_levels_label = ctk.CTkLabel(
            self.frame, text="Force Levels", font=FONT_LABEL, text_color=COLOR_TEXT
        )
        force_levels_label.grid(row=5, column=0, padx=10, pady=(10, 5), sticky="w")

        force_levels_button = ctk.CTkButton(
            self.frame,
            width=180,
            text="Generate Force Levels",
            command=self.shuffle_force_levels,
            fg_color=COLOR_BUTTON,
            hover_color=COLOR_BUTTON_HOVER,
        )
        force_levels_button.grid(row=5, column=1, padx=10, pady=(10, 5), sticky="w")

        # Display Shuffled Force Levels
        self.forces_data_label = ctk.CTkLabel(
            self.frame, text="idle", font=FONT_LABEL, text_color=COLOR_TEXT
        )
        self.forces_data_label.grid(row=6, column=0, columnspan=2, pady=(0, 10))
        
        # Target Level Button and Display
        tar_level_button = ctk.CTkButton(
            self.frame,
            width=100,
            text="Target Level",
            command=self.target_level_button,
            fg_color=COLOR_BUTTON,
            hover_color=COLOR_BUTTON_HOVER,
        )
        tar_level_button.grid(row=7, column=0, padx=10, pady=(5, 10), sticky="w")

        self.target_label = ctk.CTkLabel(
            self.frame, text="idle", font=(FONT_LABEL[0], FONT_LABEL[1], "bold"), text_color=COLOR_TEXT
        )
        self.target_label.grid(row=7, column=1, padx=10, pady=(5, 10), sticky="w")

        # Progress bar
        self.progressbar = ctk.CTkProgressBar(
            self.frame,
            width=200,
            height=15,
            fg_color="#cccccc",
            bg_color=COLOR_ENTRY_BG,
            progress_color=COLOR_TEXT,
        )
        self.progressbar.grid(row=8, column=0, columnspan=2, pady=(5, 10))
        self.progressbar.set(0)
        
        # Start and Stop Measurement Buttons
        start_button = ctk.CTkButton(
            self.frame,
            text="Start Measurement",
            command=self.NI_start_measurement,
            fg_color=COLOR_START,
            hover_color=COLOR_START_HOVER,
        )
        start_button.grid(row=9, column=0, padx=10, pady=(20, 5), sticky="w")

        stop_button = ctk.CTkButton(
            self.frame,
            text="Stop Measurement",
            command=self.NI_stop_measurement,
            fg_color=COLOR_STOP,
            hover_color=COLOR_STOP_HOVER,
        )
        stop_button.grid(row=9, column=1, padx=10, pady=(20, 5), sticky="e")
        # Participant's Number
        participant_name_label = ctk.CTkLabel(self.frame, text="Participant's Number", font=("Arial", 14), text_color="#3a3a3a")
        participant_name_label.grid(row=1, column=0, padx=10, pady=(10, 5), sticky="w")

        self.participant_number_entry = ctk.CTkEntry(self.frame, width=180, placeholder_text="Enter number", border_color="#3a3a3a", fg_color="#f0f0f0")
        self.participant_number_entry.configure(text_color="#3a3a3a")
        self.participant_number_entry.grid(row=1, column=1, padx=10, pady=(10, 5), sticky="w")
        
        # Participant's Age
        participant_age_label = ctk.CTkLabel(self.frame, text="Participant's Age", font=("Arial", 14), text_color="#3a3a3a")
        participant_age_label.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")

        self.participant_age_entry = ctk.CTkEntry(self.frame, width=180, placeholder_text="Enter Age", border_color="#3a3a3a", fg_color="#f0f0f0")
        self.participant_age_entry.configure(text_color="#3a3a3a")
        self.participant_age_entry.grid(row=2, column=1, padx=10, pady=(10, 5), sticky="w")
        

    def _create_labeled_entry(self, row: int, label_text: str, placeholder: str, attr_name: str) -> None:
        """
        Helper function to create a label and entry pair.
        """
        label = ctk.CTkLabel(self.frame, text=label_text, font=FONT_LABEL, text_color=COLOR_TEXT)
        label.grid(row=row, column=0, padx=10, pady=(10, 5), sticky="w")

        entry = ctk.CTkEntry(
            self.frame,
            width=180,
            placeholder_text=placeholder,
            border_color=COLOR_BORDER,
            fg_color=COLOR_ENTRY_BG,
        )
        entry.configure(text_color=COLOR_TEXT)
        entry.grid(row=row, column=1, padx=10, pady=(10, 5), sticky="w")

        setattr(self, attr_name, entry)

    def shuffle_force_levels(self) -> None:
        """
        Generate and display shuffled force levels.
        """
        force_levels = np.arange(20, 90, 10)
        np.random.shuffle(force_levels)
        self.repeated_force_levels = np.repeat(force_levels, 2)
        self.forces_data_label.configure(text=str(self.repeated_force_levels))
        self.tar_idx = 0
        self.progressbar.set(0)

    # Target level button functionality
    def target_level_button(self) -> None:
        """
        Update the target level and progress based on the shuffled force levels.
        """
        if self.repeated_force_levels is None:
            CTkMessagebox(title="Info", message="Force levels not generated.", icon="info")
            return
        
        if self.tar_idx < len(self.repeated_force_levels):
            current_level = self.repeated_force_levels[self.tar_idx]
            self.target_label.configure(text=str(current_level))
            self.tar_idx += 1
            progress = self.tar_idx / len(self.repeated_force_levels)
            self.progressbar.set(progress)
        else:
            self.target_label.configure(text="Measurement Complete!")
            self.tar_idx = 0

    # NI Measurement Start and Stop
    def NI_start_measurement(self) -> None:
        """
        Start the NI DAQ measurement if not already running.
        """
        if self.daq is not None:
            CTkMessagebox(title="Measurement Warning", message="Measurement already running.", icon="warning")
            return

        participant_num = self.get_participant_number()

        if not participant_num:
            CTkMessagebox(title="Error", message="Please enter a participant number", icon="cancel")
            return

        # Create participant directories and store raw EIT directory if needed
        self.raw_eit_dir, raw_iso_dir, _ = create_participant_directory(participant_num)
        human_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        iso_filename = os.path.join(raw_iso_dir, f"Participant_{participant_num}_iso_{human_time}")


        sampling_rate = 40  # Hz
        chunk_size = sampling_rate  # Number of samples per read

        self.daq = ContinuousDAQ(sampling_rate, chunk_size, iso_filename)
        self.acquisition_thread = threading.Thread(target=self.daq.start_measurement, daemon=True)
        self.acquisition_thread.start()

        CTkMessagebox(title="Measurement Info", message="Measurement started successfully.", icon="info")

    def NI_stop_measurement(self):
        """
        Stop the NI DAQ measurement if it is running.
        """
        if self.daq is None:
            CTkMessagebox(title="Measurement Warning", message="No measurement in progress", icon="warning")
            return

        self.daq.stop_measurement()
        self.daq = None  
        self.acquisition_thread = None

        CTkMessagebox(title="Measurement Info", message="Measurement stopped and data saved.", icon="info")


# Getter Methods

    def get_participant_number(self) -> str:
        """
        Return the participant number from the entry widget.
        """
        return self.participant_number_entry.get()

    def get_participant_age(self) -> str:
        """
        Return the participant age from the entry widget.
        """
        return self.participant_age_entry.get()

    def get_participant_gender(self) -> str:
        """
        Return the selected participant gender.
        """
        return self.participant_gender_box.get()

    def get_participant_leg(self) -> str:
        """
        Return the selected participant leg.
        """
        return self.participant_leg_box.get()

    def get_force_levels(self) -> str:
        """
        Return the displayed force levels.
        """
        return self.forces_data_label.cget("text")

    def get_raw_eit_dir(self) -> Optional[str]:
        """
        Return the raw EIT directory if set.
        """
        return self.raw_eit_dir
