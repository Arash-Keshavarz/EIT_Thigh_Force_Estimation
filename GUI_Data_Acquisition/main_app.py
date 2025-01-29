import customtkinter as ctk
import json
from eit_module import EITMeasurementModule
from isokinetic_module import IsokineticMeasurementModule
from protocol_generate import ExperimentProtocol
from CTkMessagebox import CTkMessagebox
import os
from utils import create_participant_directory

class MainApp(ctk.CTk):
    def __init__(self):
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

        self.protocol_button = ctk.CTkButton(self, text="Generate Protocol", command=self.generate_protocol)
        self.protocol_button.grid(row=1, column=0, padx=20, pady=20 ,columnspan=2, sticky="nsew")




    def generate_protocol(self):
        # Get data from IsokineticMeasurementModule and EITMeasurementModule
        participant_num = self.left_frame.get_participant_number()
        participant_age = self.left_frame.get_participant_age()
        participant_gender = self.left_frame.get_participant_gender()
        participant_leg = self.left_frame.get_participant_leg()
        force_levels = self.left_frame.get_force_levels()

        excitation_frequency = self.right_frame.get_parameters("Excitation Frequency (Hz)")
        burst_count = self.right_frame.get_parameters("Burst Count")
        amplitude = self.right_frame.get_parameters("Amplitude (mA)")
        frame_rate = self.right_frame.get_parameters("Frame Rate (fps)")
        injection_skip = self.right_frame.get_parameters("Injection Skip")
        note_entries = self.right_frame.get_note_entry_text()

        if not participant_num or not participant_leg or not participant_gender or not participant_age:
            CTkMessagebox(title="Error", message="Please complete all participant details before generating the protocol.", icon="cancel")
            return
        
        # create participant directory
        participant_dir = create_participant_directory(participant_num)

        # create a directory to store data
        protocol_data = {
            "participant" : {
                "Number": participant_num,
                "age" : participant_age,
                "gender": participant_gender,
                "leg": participant_leg
            },
            "isokinetic_measurement":{
                "rotations_velocity":"30 °/s",
                "force_levels": force_levels
            },
            "eit_measurement":{
                "excitation_frequency": 125_000, ## modify if needed
                "burst_count": 0,
                "amplitude": "1 mA",
                "frame_rate": 40,
                "n_el": 16,
                "injection_skip": 5
            },
            "notes": note_entries
        }

        # save Json file
        self.save_json(participant_dir, participant_num, protocol_data
                       )
        # Create the Protocol
        protocol = ExperimentProtocol(
            title="Experiment Protocol: Force/EIT Measurement"
            , experimenter= "University of Rostock"
            )  # Edit experimenter
        
        # Add an introductory section
        protocol.add_section(
            "Objective of the Experiment",
            "The objective is to record Torque, leg angle, and EIT data in parallel.",
        )

        # Add participant details section
        participant_details = (
        f"{'Participant Number: ':<5}{participant_num:<25}"
        f"{'Age:':<5}{participant_age:<25}"
        f"{'Gender:':<5}{participant_gender:<25}"
        f"{'Leg:':<5}{participant_leg:<25}"
        )
        protocol.add_section(
            "Participant Details", participant_details)


        # Add Isokinetic Measurement section
        isokinetic_setup = (f"Rotation Velocity: 30 °/s \n"
                            f"Force Levels: {force_levels}")
        protocol.add_section(
            "IsoKinetic Dynommeter Measurement Setup: ", isokinetic_setup)

        # Add EIT Measurement section
        eit_setup = (
            f"Excitation Frequency: {excitation_frequency} Hz \n"
            f"Burst Count: {burst_count} \n"
            f"Amplitude: {amplitude} mA \n"
            f"Frame Rate: {frame_rate} fps \n"
            f"Injection Skip: {injection_skip}"
        )
        protocol.add_section(
            "EIT Measurement Setup: ", eit_setup)   

        protocol.add_section(
            "Notes during the Experiment",
            note_entries
        )     
        # Generate the PDF file
        pdf_filename = os.path.join(participant_dir, f"Participant_{participant_num}_protocol.pdf")
        protocol.generate_pdf(pdf_filename)
        
        CTkMessagebox(title="Success", message=f"Protocol saved as {pdf_filename}.", icon="check", option_1="OK")

    def save_json(self, participant_dir, participant_num, data):
        json_filename = os.path.join(participant_dir, f"Participant_{participant_num}_protocol.json")

        with open(json_filename, "w") as json_file:
            json.dump(data, json_file, indent=4)

    
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
