import numpy as np
import customtkinter as ctk
import json
from CTkMessagebox import CTkMessagebox
from NI_module import ContinuousDAQ
from utils import create_participant_directory
import threading
import os

class IsokineticMeasurementModule:
    def __init__(self, parent):
        
        self.frame = ctk.CTkFrame(parent)
        self.frame.grid(row=0, column=0, padx=20, pady=20)
        self.frame.grid_columnconfigure(0, weight=0)  # Label column
        self.frame.grid_columnconfigure(1, weight=1)  # Entry column

        
        # Initialize DAQ attributes
        self.daq = None
        self.acquisition_thread = None

        # Create content for IsokineticMeasurementModule
        self.create_content()

    def create_content(self):
        
        # Title Label
        title_label = ctk.CTkLabel(self.frame, text="Isokinetic Measurement Config", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Participant's Name
        participant_name_label = ctk.CTkLabel(self.frame, text="Participant's Number", font=("Arial", 14))
        participant_name_label.grid(row=1, column=0, padx=5, pady=(10, 5), sticky="w")

        self.participant_name_entry = ctk.CTkEntry(self.frame, width=150, placeholder_text="Enter Name")
        self.participant_name_entry.grid(row=1, column=1, padx=5, pady=(10, 5), sticky="w")
        
        # Participant's Age
        participant_age_label = ctk.CTkLabel(self.frame, text="Participant's Age", font=("Arial", 14))
        participant_age_label.grid(row=2, column=0, padx=5, pady=(10, 5), sticky="w")

        self.participant_age_entry = ctk.CTkEntry(self.frame, width=150, placeholder_text="Enter Age")
        self.participant_age_entry.grid(row=2, column=1, padx=5, pady=(10, 5), sticky="w")
        
        # Participant's Gender
        participant_gender_label = ctk.CTkLabel(self.frame, text="Participant's Gender", font=("Arial", 14))
        participant_gender_label.grid(row=3, column=0, padx=5, pady=(10, 5), sticky="w")
        
        self.participant_gender_box = ctk.CTkComboBox(self.frame, width=150, values= ["male", "female"])
        self.participant_gender_box.grid(row=3, column=1, padx=5, pady=(10, 5), sticky="w")
        
        # Participant's Leg
        participant_leg_label = ctk.CTkLabel(self.frame, text="Participant's Leg", font=("Arial", 14))
        participant_leg_label.grid(row=4, column=0, padx=5, pady=(10, 5), sticky="w")

        self.participant_leg_box = ctk.CTkComboBox(self.frame, width=150, values=["right", "left"])
        self.participant_leg_box.grid(row=4, column=1, padx=5, pady=(10, 5), sticky="w")


        # Shuffle the Force Levels
        force_levels_label = ctk.CTkLabel(self.frame, text="Force Levels", font=("Arial", 14))
        force_levels_label.grid(row=5, column=0, padx=5, pady=(10, 5), sticky="w")

        force_levels_button = ctk.CTkButton(self.frame,width=150, text="Generate the Force Levels", command=self.shuffle_force_levels)
        force_levels_button.grid(row=5, column=1, padx=5, pady=(10, 5), sticky="w")

        # Display the Shuffled Force Levels
        self.forces_data_label = ctk.CTkLabel(self.frame, text= "idle", font=("Arial", 14))
        self.forces_data_label.grid(row=6, column=0, columnspan=2, pady=20)

        # Start NI measurement Button
        save_button = ctk.CTkButton(self.frame, text="Start Measurement", command=self.NI_start_measurement)
        save_button.grid(row=7, column=0, columnspan=2, pady=20)
        # Stop NI measurement Button
        save_button = ctk.CTkButton(self.frame, text="Stop Measurement", command=self.NI_stop_measurement)
        save_button.grid(row=8, column=0, columnspan=2, pady=20)        


    def shuffle_force_levels(self):
        # Generate random force levels and show them in the GUI
        force_levels = np.arange(10, 90, 10)
        np.random.shuffle(force_levels)
        repeated_force_levels = np.repeat(force_levels, 2)  # Repeat the force levels twice

    
        # Update the forces_data_label with the shuffled force levels
        self.forces_data_label.configure(text=str(repeated_force_levels))

    def NI_start_measurement(self):
            """
            Start the measurement process using ContinuousDAQ.
            """
            if self.daq is not None:
                CTkMessagebox.show_warning("Measurement Warning", "Measurement already running.")
                return
            
            participant_name = self.get_participant_name()

            if not participant_name:
                CTkMessagebox(title="Error", message="Please enter a participant name", icon="cancel")

            participant_dir = create_participant_directory(participant_name)
            ni_data_filename = os.path.join(participant_dir, f"{participant_name}_NI_data.npz")

            #################### Adjust the parameters if neeeded ########################
            sampling_rate = 500  # Hz
            chunk_size = 500  # Number of samples per read

            self.daq = ContinuousDAQ(sampling_rate, chunk_size, ni_data_filename)

            # Run DAQ in a separate thread to keep GUI responsive
            self.acquisition_thread = threading.Thread(target=self.daq.start_measurement, daemon=True)
            self.acquisition_thread.start()

            CTkMessagebox(title="Measurement Info", message="Measurement started successfully.", icon="info")

    def NI_stop_measurement(self):
        """
        Stop the measurement process.
        """
        if self.daq is None:
            
            CTkMessagebox(title="Measurement Warning", message="No measurement in progress", icon="warning")
            return

        # Stop the DAQ acquisition
        self.daq.stop_measurement()

        # Reset DAQ instance and thread
        self.daq = None
        self.acquisition_thread = None

        CTkMessagebox(title="Measurement Info", message="Measurement stopped and data saved.", icon="info")  


    # Getter Methods
    def get_participant_name(self):
        return self.participant_name_entry.get()

    def get_participant_age(self):
        return self.participant_age_entry.get()
    
    def get_participant_gender(self):
        return self.participant_gender_box.get()
    
    def get_participant_leg(self):
        return self.participant_leg_box.get()

    def get_force_levels(self):
        return self.forces_data_label.cget("text")
