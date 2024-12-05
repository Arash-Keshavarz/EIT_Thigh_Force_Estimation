import customtkinter as ctk
import json
from eit_module import EITMeasurementModule
from isokinetic_module import IsokineticMeasurementModule


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("EIT/Isokinetic Measurement System")
        self.geometry("1000x600")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0,1), weight=1)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")  # Set color theme
        
        self.left_frame = IsokineticMeasurementModule(self)
        
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nse")




if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
