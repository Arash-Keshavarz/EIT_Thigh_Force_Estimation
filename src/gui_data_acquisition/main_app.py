"""
main_app.py

Main application file for the EIT/Isokinetic Measurement System.
This module creates the main window, integrates measurement modules,
and provides functionality for generating experimental protocols.
"""

import os
import json
import logging
from typing import Any, Dict

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from eit_module import EITMeasurementModule
from isokinetic_module import IsokineticMeasurementModule
from utils import create_participant_directory, ExperimentProtocol

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)



class MainApp(ctk.CTk):
    """
    Main application window that integrates the EIT and Isokinetic measurement modules,
    and provides protocol generation functionality.
    """
    def __init__(self) -> None:
        """
        Initialize the main application window, configure appearance, and place modules.
        """
        super().__init__()

        ## Initial settings    
        self.title("EIT/Isokinetic Measurement System")
        self.geometry("800x600")
        self.iconbitmap('asset/logo.ico')
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)  

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")  


        # Left Frame: IsokineticMeasurementModule
        self.left_frame = IsokineticMeasurementModule(self)
        
        self.left_frame.frame.grid(row=0, column=0, padx=10, pady=(10, 40), sticky="nsew")  # Place in left column
        
        # Right Frame: EITMeasurementModule
        self.right_frame = EITMeasurementModule(self)
        self.right_frame.frame.grid(row=0, column=1, padx=10, pady=(10, 40), sticky="nsew")  # Place in right column

        ################################################################
        # Button to Generate The Protocol
        self.protocol_button = ctk.CTkButton(
            self,
            text="Generate Protocol",
            command=self.generate_protocol
        )
        self.protocol_button.grid(row=1, column=0, padx=20, pady=20, columnspan=2, sticky="nsew")

    def generate_protocol(self) -> None:
        """
        Gather data from measurement modules, generate a protocol,
        save it as JSON and PDF, and display a confirmation message.
        """
        # Get data from IsokineticMeasurementModule
        participant_num = self.left_frame.get_participant_number().strip()
        participant_age = self.left_frame.get_participant_age().strip()
        participant_gender = self.left_frame.get_participant_gender().strip()
        participant_leg = self.left_frame.get_participant_leg().strip()
        force_levels = self.left_frame.get_force_levels().strip()

        # Get parameters from EITMeasurementModule
        excitation_frequency = self.right_frame.get_parameters("Excitation Frequency (Hz)").strip()
        burst_count = self.right_frame.get_parameters("Burst Count").strip()
        amplitude = self.right_frame.get_parameters("Amplitude (mA)").strip()
        frame_rate = self.right_frame.get_parameters("Frame Rate (fps)").strip()
        injection_skip = self.right_frame.get_parameters("Injection Skip").strip()
        note_entries = self.right_frame.get_note_entry_text()

        # Check for missing participant details
        if not all([participant_num, participant_age, participant_gender, participant_leg]):
            CTkMessagebox(
                title="Error",
                message="Please complete all participant details before generating the protocol.",
                icon="cancel"
            )
            return

        logging.info("Generating protocol for participant %s", participant_num)

        # Create participant directory (assumes create_participant_directory returns a tuple)
        _,_, participant_dir = create_participant_directory(participant_num)

        # Build protocol data
        protocol_data: Dict[str, Any] = {
            "participant": {
                "Number": participant_num,
                "age": participant_age,
                "gender": participant_gender,
                "leg": participant_leg
            },
            "isokinetic_measurement": {
                "rotation_velocity": "30 °/s",
                "force_levels": force_levels
            },
            "eit_measurement": {
                "excitation_frequency": 125_000,  # Modify if needed
                "burst_count": 0,
                "amplitude": "1 mA",
                "frame_rate": 40,
                "n_el": 16,
                "injection_skip": 5
            },
            "notes": note_entries
        }

        # Save protocol data as JSON
        self.save_json(participant_dir, participant_num, protocol_data)

        # Create the protocol using ExperimentProtocol
        protocol = ExperimentProtocol(
            title="Experiment Protocol: IsoForce/EIT Measurement",
            experimenter="University of Rostock"  # Edit experimenter if needed
        )

        # Add sections to the protocol
        protocol.add_section(
            "Objective of the Experiment",
            "The objective is to record torque, leg angle, and speed from the Isoforce device while simultaneously measuring EIT data."
        )

        participant_details = (
            f"Participant Number: {participant_num:<25}\n"
            f"Age: {participant_age:<25}\n"
            f"Gender: {participant_gender:<25}\n"
            f"Leg: {participant_leg:<25}"
        )
        protocol.add_section("Participant Details", participant_details)

        isokinetic_setup = (
            "Rotation Velocity: 30 °/s\n"
            f"Force Levels: {force_levels}"
        )
        protocol.add_section("Isokinetic Dynommeter Measurement Setup", isokinetic_setup)

        eit_setup = (
            f"Excitation Frequency: {excitation_frequency} Hz\n"
            f"Burst Count: {burst_count}\n"
            f"Amplitude: {amplitude} mA\n"
            f"Frame Rate: {frame_rate} fps\n"
            f"Injection Skip: {injection_skip}"
        )
        protocol.add_section("EIT Measurement Setup", eit_setup)

        protocol.add_section("Notes during the Experiment", note_entries)

        # Generate PDF file for the protocol
        pdf_filename = os.path.join(participant_dir, f"Participant_{participant_num}_protocol.pdf")
        protocol.generate_pdf(pdf_filename)
        logging.info("Protocol PDF generated at %s", pdf_filename)

        CTkMessagebox(
            title="Success",
            message=f"Protocol saved as {pdf_filename}.",
            icon="check",
            option_1="OK"
        )
    

    def save_json(self, participant_dir: str, participant_num: str, data: Dict[str, Any]) -> None:
        """
        Save the protocol data as a JSON file in the participant directory.

        Args:
            participant_dir (str): Directory where the protocol should be saved.
            participant_num (str): Participant number (used in filename).
            data (Dict[str, Any]): The protocol data to save.
        """
        json_filename = os.path.join(participant_dir, f"Participant_{participant_num}_protocol.json")
        try:
            with open(json_filename, "w") as json_file:
                json.dump(data, json_file, indent=4)
            logging.info("Protocol JSON saved at %s", json_filename)
        except Exception as e:
            logging.error("Error saving protocol JSON: %s", e)

    
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
