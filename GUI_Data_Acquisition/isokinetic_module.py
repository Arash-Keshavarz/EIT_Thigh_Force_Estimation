import numpy as np
import customtkinter as ctk
import json
from CTkMessagebox import CTkMessagebox
from NI_module import ContinuousDAQ
from utils import create_participant_directory
import threading
import os
import datetime
import time

class IsokineticMeasurementModule:
    def __init__(self, parent):
        self.frame = ctk.CTkFrame(parent, corner_radius=15, fg_color="#e0e0e0")
        self.frame.grid(row=0, column=0, padx=20, pady=20)
        self.frame.grid_columnconfigure(0, weight=0)  # Label column
        self.frame.grid_columnconfigure(1, weight=1)  # Entry column

        # Initialize DAQ attributes
        self.daq = None
        self.acquisition_thread = None
        self.repeated_force_levels = None # to store the force levels
        self.tar_idx = 0
        
        # Create content for IsokineticMeasurementModule
        self.create_content()

    def create_content(self):
        # Title Label with custom font and color
        title_label = ctk.CTkLabel(self.frame, text="Isokinetic Measurement Config", font=("Arial", 20, "bold"), text_color="#3a3a3a")
        title_label.grid(row=0, column=0, columnspan=2, pady=20)

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
        
        # Participant's Gender
        participant_gender_label = ctk.CTkLabel(self.frame, text="Participant's Gender", font=("Arial", 14), text_color="#3a3a3a")
        participant_gender_label.grid(row=3, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.participant_gender_box = ctk.CTkComboBox(self.frame, width=180, values=["male", "female"],
                                                      border_color="#3a3a3a", fg_color= '#f0f0f0',
                                                       dropdown_fg_color="#f0f0f0", button_color="#3a3a3a",
                                                       text_color='#3a3a3a', dropdown_text_color='#333333',)
        
        self.participant_gender_box.grid(row=3, column=1, padx=10, pady=(10, 5), sticky="w")
        
        # Participant's Leg
        participant_leg_label = ctk.CTkLabel(self.frame, text="Participant's Leg", font=("Arial", 14), text_color="#3a3a3a")
        participant_leg_label.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="w")

        self.participant_leg_box = ctk.CTkComboBox(self.frame, width=180, values=["right", "left"], 
                                                    border_color="#3a3a3a", fg_color= '#f0f0f0',
                                                       dropdown_fg_color="#f0f0f0", button_color="#3a3a3a",
                                                       text_color='#3a3a3a', dropdown_text_color='#333333',)
        self.participant_leg_box.grid(row=4, column=1, padx=10, pady=(10, 5), sticky="w")

        # Force Levels Button with stylish color and hover effect
        force_levels_label = ctk.CTkLabel(self.frame, text="Force Levels", font=("Arial", 14), text_color="#3a3a3a")
        force_levels_label.grid(row=5, column=0, padx=10, pady=(10, 5), sticky="w")

        force_levels_button = ctk.CTkButton(self.frame, width=180, text="Generate Force Levels", command=self.shuffle_force_levels, fg_color="#6c757d", hover_color="#5a6268")
        force_levels_button.grid(row=5, column=1, padx=10, pady=(10, 5), sticky="w")

        # Display Shuffled Force Levels
        self.forces_data_label = ctk.CTkLabel(self.frame, text="idle", font=("Arial", 14), text_color="#3a3a3a")
        self.forces_data_label.grid(row=6, column=0, columnspan=2, pady=(0,10))

        # Target Level Button
        tar_level_button = ctk.CTkButton(self.frame, width=100, text="Target Level", command=self.target_level_button, fg_color="#6c757d", hover_color="#5a6268")
        tar_level_button.grid(row=7, column=0, padx=10, pady=(5, 10), sticky="w")

        # Display Target Level
        self.target_label = ctk.CTkLabel(self.frame, text="idle", font=("Arial", 14, "bold"), text_color="#3a3a3a")
        self.target_label.grid(row=7, column=1, padx=10, pady=(5, 10), sticky="w")

        # Progress bar with custom style
        self.progressbar = ctk.CTkProgressBar(self.frame, width=200, height=15, fg_color="#cccccc", bg_color="#f0f0f0", progress_color="#3a3a3a")
        self.progressbar.grid(row=8, column=0, columnspan=2, pady=(5, 10))
        self.progressbar.set(0)

        # Start NI Measurement Button
        save_button = ctk.CTkButton(self.frame, text="Start Measurement", command=self.NI_start_measurement, fg_color="#1F6F2b", hover_color="#166424")
        save_button.grid(row=9, column=0, padx= 10, columnspan=2, pady=(20, 5), sticky="w")

        # Stop NI Measurement Button
        stop_button = ctk.CTkButton(self.frame, text="Stop Measurement", command=self.NI_stop_measurement, fg_color="#dc3545", hover_color="#ff4d4d")
        stop_button.grid(row=9, column=1,padx=10, columnspan=2, pady=(20,5), sticky="e")

    # Shuffle force levels
    def shuffle_force_levels(self):
        force_levels = np.arange(20, 90, 10)
        np.random.shuffle(force_levels)
        self.repeated_force_levels = np.repeat(force_levels, 2)

        self.forces_data_label.configure(text=str(self.repeated_force_levels))
        self.tar_idx = 0
        self.progressbar.set(0)

    # Target level button functionality
    def target_level_button(self):
        if self.repeated_force_levels is None:
            print("Force levels not generated.")
            return

        if self.tar_idx < len(self.repeated_force_levels):
            self.target_label.configure(text=str(self.repeated_force_levels[self.tar_idx]))
            self.tar_idx += 1
            progress = self.tar_idx / len(self.repeated_force_levels)
            self.progressbar.set(progress)
        else:
            print("Measurement finished!")
            self.target_label.configure(text="Measurement Complete!")
            self.tar_idx = 0

    # NI Measurement Start and Stop
    def NI_start_measurement(self):
        if self.daq is not None:
            CTkMessagebox(title="Measurement Warning", message="Measurement already running.", icon="warning")
            return

        participant_num = self.get_participant_number()

        if not participant_num:
            CTkMessagebox(title="Error", message="Please enter a participant number", icon="cancel")
            return

        participant_dir = create_participant_directory(participant_num)
        raw_iso_dir = os.path.join(participant_dir, "Isokinetic_raw")
        raw_eit_dir = os.path.join(participant_dir, "EIT_raw")

        if not os.path.exists(raw_iso_dir):
            os.makedirs(raw_iso_dir, exist_ok=True)
        if not os.path.exists(raw_eit_dir):
            os.makedirs(raw_eit_dir, exist_ok=True)

        human_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        iso_filename = os.path.join(raw_iso_dir, f"Participant_{participant_num}_iso_{human_time}")

        sampling_rate = 40  # Hz
        chunk_size = sampling_rate  # Number of samples per read

        self.daq = ContinuousDAQ(sampling_rate, chunk_size, iso_filename)
        self.acquisition_thread = threading.Thread(target=self.daq.start_measurement, daemon=True)
        self.acquisition_thread.start()

        CTkMessagebox(title="Measurement Info", message="Measurement started successfully.", icon="info")

    def NI_stop_measurement(self):
        if self.daq is None:
            CTkMessagebox(title="Measurement Warning", message="No measurement in progress", icon="warning")
            return

        self.daq.stop_measurement()
        self.daq = None  
        self.acquisition_thread = None

        CTkMessagebox(title="Measurement Info", message="Measurement stopped and data saved.", icon="info")



    # Getter Methods
    def get_participant_number(self):
        return self.participant_number_entry.get()

    def get_participant_age(self):
        return self.participant_age_entry.get()

    def get_participant_gender(self):
        return self.participant_gender_box.get()

    def get_participant_leg(self):
        return self.participant_leg_box.get()

    def get_force_levels(self):
        return self.forces_data_label.cget("text")
