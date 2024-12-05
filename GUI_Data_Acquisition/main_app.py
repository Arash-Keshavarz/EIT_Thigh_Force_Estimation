import customtkinter as ctk
import json
from eit_module import EITMeasurementModule
from isokinetic_module import IsokineticMeasurementModule


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("EIT/Isokinetic Measurement System")
        self.geometry("800x600")
        self.grid_columnconfigure((0, 1), weight=1)  # Two columns with equal weight
        self.grid_rowconfigure(0, weight=1)  # One row

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")  # Set color theme


        # Left Frame: IsokineticMeasurementModule
        self.left_frame = IsokineticMeasurementModule(self)
        self.left_frame.frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")  # Place in left column

        # Right Frame: EITMeasurementModule
        self.right_frame = EITMeasurementModule(self)
        self.right_frame.frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")  # Place in right column

        



if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
