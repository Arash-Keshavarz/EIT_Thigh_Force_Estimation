from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from sciopy import EIT_16_32_64_128, EitMeasurementSetup
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from datetime import datetime

class EITMeasurementModule:
    def __init__(self, parent):

        self.frame = ctk.CTkFrame(parent)
        self.frame.grid(row=0, column=0, padx=20, pady=20)
        self.frame.grid_columnconfigure(0, weight=0)  # Label column
        self.frame.grid_columnconfigure(1, weight=1)  # Entry column
        
        # Title Label
        title_label = ctk.CTkLabel(self.frame, text="EIT Measurement Config", font=("Arial", 18))
        title_label.grid(row=0, column=0, columnspan=2, pady=10) 

        # Parameter Inputs

        self.create_parameter_inputs()
        
         # Note Area
        self.note_frame = ctk.CTkFrame(self.frame, width=400, height=100)
        self.note_frame.grid(row=len(self.entries) + 1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.note_entry = ctk.CTkEntry(self.note_frame, placeholder_text="Notes during the experiment")
        self.note_entry.pack(padx=10, pady=10, fill="both", expand=True)

        # Start Button
        self.start_button = ctk.CTkButton(self.frame, text="Start EIT Measurement", command=self.start_measurement)
        self.start_button.grid(row=len(self.entries) + 2, column=0, columnspan=2, pady=20, sticky="n")

    
    def create_parameter_inputs(self):
        params = {
            "Excitation Frequency (Hz)": "125_000",
            "Burst Count": "1",
            "Amplitude (mA)": "0.01",
            "Frame Rate (fps)": "3",
            "Injection Skip": "n_el // 2",
        }
        self.entries = {}
        for i, (label, default) in enumerate(params.items()):

            lbl = ctk.CTkLabel(self.frame, text=label, font=("Arial", 14))
            lbl.grid(row=i + 1, column=0, padx=10, pady=(10, 5), sticky="w")  
            entry = ctk.CTkEntry(self.frame, placeholder_text=default)
            entry.grid(row=i + 1, column=1, padx=10, pady=(10, 5), sticky="w")
            self.entries[label] = entry

    def start_measurement(self):
        # Extract Parameters
        try:
            params = {key: float(entry.get()) for key, entry in self.entries.items()}
            data = self.perform_measurement(params)
            self.plot_results(data)
            CTkMessagebox(title="Success", message=f"Measurement complete.", icon="check", option_1="OK")

        except Exception as e:
            CTkMessagebox(title="Error", message=f"Error: {e}", icon="cancel")

    def perform_measurement(self, params, save_path="measurement_data.npz"):
        n_el = 16
        sciospec = EIT_16_32_64_128(n_el)
        sciospec.connect_device_HS()
        sciospec.SystemMessageCallback()
        #sciospec.GetDeviceInfo()        
        setup = EitMeasurementSetup(
            burst_count = int(params["Burst Count"]),
            n_el = n_el,
            exc_freq = params["Excitation Frequency (Hz)"],
            framerate = int(params["Frame Rate (fps)"]),
            amplitude = params["Amplitude (mA)"],
            inj_skip = n_el // 2,
            gain = 1,
            adc_range = 1,
        )
        sciospec.SetMeasurementSetup(setup)
        #sciospec.GetMeasurementSetup(2)
        data = sciospec.StartStopMeasurement(return_as="pot_mat")
        #sciospec.SoftwareReset()
        
        current_date = datetime.now().isoformat()
        np.savez(save_path, data=data, datetime=current_date)

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
        return self.note_entry.get()