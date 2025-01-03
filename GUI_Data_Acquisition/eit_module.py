from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from sciopy import EIT_16_32_64_128, EitMeasurementSetup
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from datetime import datetime
import os
import time

class EITMeasurementModule:
    def __init__(self, parent):

        self.frame = ctk.CTkFrame(parent)
        self.frame.grid(row=0, column=0, padx=20, pady=20)
        self.frame.grid_columnconfigure(0, weight=0)  # Label column
        self.frame.grid_columnconfigure(1, weight=1)  # Entry column
        
        # Title Label
        title_label = ctk.CTkLabel(self.frame, text="EIT Measurement Config", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10) 

        # Parameter Inputs

        self.create_parameter_inputs()
        
         # Note Area
        #self.note_frame = ctk.CTkFrame(self.frame, width=400, height=400)
        #self.note_frame.grid(row=len(self.entries) + 1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.note_entry = ctk.CTkTextbox(self.frame, width = 400, height=100, corner_radius=5)
        self.note_entry.insert("0.0", "Notes during the experiment")
        self.note_entry.bind("<FocusIn>", lambda e: self.clear_placeholder())  # Clear placeholder on focus
        #self.note_entry = ctk.CTkEntry(self.frame, width = 400, height=100, placeholder_text="Notes during the experiment")
        self.note_entry.grid(row=len(self.entries) + 1, padx=10, pady=10, sticky="nsew", columnspan=2)

        # Start Button
        self.start_button = ctk.CTkButton(self.frame, text="Start EIT Measurement", command=self.start_measurement)
        self.start_button.grid(row=len(self.entries) + 2, column=0, columnspan=2, pady=20, sticky="n")

    def clear_placeholder(self):
        if self.note_entry.get("0.0", "end").strip() == "Notes during the experiment":
            self.note_entry.delete("0.0", "end")

    def create_parameter_inputs(self):
        params = {
            "Excitation Frequency (Hz)": "125_000",
            "Burst Count": "1",
            "Amplitude (mA)": "0.01",
            "Frame Rate (fps)": "3",
            "Injection Skip": "n_el // 2",
            "Force Level": "[20-80]"
        }
        self.entries = {}
        for i, (label, default) in enumerate(params.items()):

            lbl = ctk.CTkLabel(self.frame, text=label, font=("Arial", 14))
            lbl.grid(row=i + 1, column=0, padx=5, pady=(10, 5), sticky="w")  
            entry = ctk.CTkEntry(self.frame, width=150, placeholder_text=default)
            entry.grid(row=i + 1, column=1, padx=5, pady=(10, 5), sticky="w")
            self.entries[label] = entry

    def start_measurement(self):
        # Extract Parameters
        try:
            params = {key: float(entry.get()) for key, entry in self.entries.items()}
            self.perform_measurement(params)
            #self.plot_results(data)
            CTkMessagebox(title="Success", message=f"Measurement complete.", icon="check", option_1="OK")

        except Exception as e:
            CTkMessagebox(title="Error", message=f"Error: {e}", icon="cancel")


    def perform_measurement(self, params, save_dir="measurements"):
        # Ensure the save directory exists
        os.makedirs(save_dir, exist_ok=True)

        # Determine the next available filename
        files = [f for f in os.listdir(save_dir) if f.startswith("sample_") and f.endswith(".npz")]
        if files:
            max_index = max(int(f.split("_")[1].split(".")[0]) for f in files)
        else:
            max_index = -1

        next_index = max_index + 1
        save_path = os.path.join(save_dir, f"sample_{next_index:05d}.npz")

        # Perform the measurement
        n_el = 16
        sciospec = EIT_16_32_64_128(n_el)
        sciospec.connect_device_HS()
        sciospec.SystemMessageCallback()

        setup = EitMeasurementSetup(
            burst_count=int(params["Burst Count"]),
            n_el=n_el,
            exc_freq=params["Excitation Frequency (Hz)"],
            framerate=int(params["Frame Rate (fps)"]),
            amplitude=params["Amplitude (mA)"],
            inj_skip=n_el // 2,
            gain=1,
            adc_range=1,
        )
        sciospec.SetMeasurementSetup(setup)

        # record start time
        start_timestamp = time.time()
        data = sciospec.StartStopMeasurement(return_as="pot_mat")
        # record end time
        end_timestamp = time.time()

        # Save the data
        np.savez(save_path, data=data, start_timestamp=start_timestamp, end_timestamp= end_timestamp, force_level=params["Force Level"])

        return data


    ## not used
    def plot_results(self, data):
        # Clear previous plots
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        # Plot data
        fig, ax = plt.subplots(figsize=(3, 3))
        ax.imshow(np.abs(data[0]), cmap="viridis")
        ax.set_title("EIT Measurement Results")

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)



    ## Getter Methods
    def get_parameters(self, parameter_name):

        """Retrieves the value of a specified parameter."""

        if parameter_name in self.entries:
            return self.entries[parameter_name].get()
        else:
            raise ValueError(f"Parameter '{parameter_name}' not found.")
    def get_note_entry_text(self):
        return self.note_entry.get("0.0", "end").strip()