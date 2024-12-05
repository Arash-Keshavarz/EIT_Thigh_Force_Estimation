import customtkinter as ctk
import json
from eit_module import EITMeasurementModule
from isokinetic_module import IsokineticMeasurementModule
from protocol_generate import ExperimentProtocol
from CTkMessagebox import CTkMessagebox

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("EIT/Isokinetic Measurement System")
        self.geometry("800x600")
        self.grid_columnconfigure((0, 1), weight=1)  # Two columns with equal weight
        self.grid_rowconfigure((0, 1), weight=1)  # One row

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")  # Set color theme


        # Left Frame: IsokineticMeasurementModule
        self.left_frame = IsokineticMeasurementModule(self)
        self.left_frame.frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")  # Place in left column

        # Right Frame: EITMeasurementModule
        self.right_frame = EITMeasurementModule(self)
        self.right_frame.frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")  # Place in right column

        ################################################################
        # Button to Generate The Protocol

        self.protocol_button = ctk.CTkButton(self, text="Generate Protocol", command=self.generate_protocol)
        self.protocol_button.grid(row=1, column=0, columnspan=2, pady=20)
        



    def generate_protocol(self):
        # Get data from IsokineticMeasurementModule and EITMeasurementModule
        participant_name = self.left_frame.get_participant_name()
        participant_leg = self.left_frame.get_participant_leg()

        if not participant_name or not participant_leg:
            CTkMessagebox(title="Error", message="Please complete all participant details before generating the protocol.", icon="cancel")
            return
        
        # Create the Protocol
        protocol = ExperimentProtocol(
            title="Experiment Protocol: Force/EIT Measurement"
            , experimenter= "Arash"
            )  # Edit experimenter
        
        # Add an introductory section
        protocol.add_section(
            "Objective of the Experiment",
            "The objective is to record Torque, leg angle, and EIT data in parallel.",
        )

        # Add participant details section
        protocol.add_section(
            "Participant Details",
            f"Name: {participant_name}\nLeg: {participant_leg}",
        )

        # Add Isokinetic Measurement section
        protocol.add_section(
            "EIT Measurement Setup: ",
            "..."
        )

        # Add EIT Measurement section
        protocol.add_section(
            "Isokinetic Measurement Setup: ",
            "..."
        )        
        # Generate the PDF file
        pdf_filename = f"{protocol.experimenter}_protocol.pdf"
        protocol.generate_pdf(pdf_filename)
        
        CTkMessagebox(title="Success", message=f"Protocol saved as {pdf_filename}.", icon="check", option_1="OK")


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
