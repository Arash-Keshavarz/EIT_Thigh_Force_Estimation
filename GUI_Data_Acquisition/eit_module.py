from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from sciopy import EIT_16_32_64_128, EitMeasurementSetup
import customtkinter as ctk

class EITMeasurementModule:
    def __init__(self, parent):
        self.frame = ctk.CTkFrame(parent)
        self.frame.pack(fill="both", expand=True)

        # Parameter Inputs
        self.create_parameter_inputs()
        self.status_label = ctk.CTkLabel(self.frame, text="Status: Idle")
        self.status_label.pack(pady=10)

        # Plot Area
        self.plot_frame = ctk.CTkFrame(self.frame)
        self.plot_frame.pack(fill="both", expand=True)

        # Start Button
        self.start_button = ctk.CTkButton(self.frame, text="Start EIT Measurement", command=self.start_measurement)
        self.start_button.pack(pady=20)

    def create_parameter_inputs(self):
        params = {
            "Excitation Frequency (Hz)": "125000",
            "Burst Count": "1",
            "Amplitude (mA)": "0.01",
            "Frame Rate (fps)": "3",
        }
        self.entries = {}
        for i, (label, default) in enumerate(params.items()):
            lbl = ctk.CTkLabel(self.frame, text=label)
            lbl.grid(row=i, column=0, padx=10, pady=5)
            entry = ctk.CTkEntry(self.frame, placeholder_text=default)
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entries[label] = entry

    def start_measurement(self):
        # Extract Parameters
        try:
            params = {key: float(entry.get()) for key, entry in self.entries.items()}
            data = self.perform_measurement(params)
            self.plot_results(data)
            self.status_label.configure(text="Measurement complete.")
        except Exception as e:
            self.status_label.configure(text=f"Error: {e}")

    def perform_measurement(self, params):
        n_el = 16
        sciospec = EIT_16_32_64_128(n_el)
        sciospec.connect_device_HS()
        setup = EitMeasurementSetup(
            burst_count=int(params["Burst Count"]),
            n_el=n_el,
            exc_freq=int(params["Excitation Frequency (Hz)"]),
            framerate=int(params["Frame Rate (fps)"]),
            amplitude=params["Amplitude (mA)"],
            inj_skip=n_el // 2,
            gain=1,
            adc_range=1,
        )
        sciospec.SetMeasurementSetup(setup)
        data = sciospec.StartStopMeasurement(return_as="pot_mat")
        sciospec.SoftwareReset()
        return data

    def plot_results(self, data):
        # Clear previous plots
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        # Plot data
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.imshow(np.abs(data[0]), cmap="viridis")
        ax.set_title("EIT Measurement Results")

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
