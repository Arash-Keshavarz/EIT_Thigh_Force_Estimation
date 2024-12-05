import customtkinter as ctk
import json

class IsokineticMeasurementModule:
    def __init__(self, parent):
        
        self.frame = ctk.CTkFrame(parent)
        self.frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsw")

        # Create content for IsokineticMeasurementModule
        self.create_content()

    def create_content(self):
        # Title Label
        title_label = ctk.CTkLabel(self.frame, text="Isokinetic Measurement Config", font=("Arial", 18))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Participant's Name
        participant_name_label = ctk.CTkLabel(self.frame, text="Participant's Name:", font=("Arial", 14))
        participant_name_label.grid(row=1, column=0, padx=10, pady=(10, 5), sticky="w")

        self.participant_name_entry = ctk.CTkEntry(self.frame, width=300, placeholder_text="Enter Name")
        self.participant_name_entry.grid(row=2, column=0, padx=10, pady=(10, 5))

        # Participant's Leg
        participant_leg_label = ctk.CTkLabel(self.frame, text="Participant's Leg:", font=("Arial", 14))
        participant_leg_label.grid(row=3, column=0, padx=10, pady=(10, 5), sticky="w")

        self.participant_leg_entry = ctk.CTkEntry(self.frame, width=300, placeholder_text="Enter Leg")
        self.participant_leg_entry.grid(row=4, column=0, padx=10, pady=(10, 5))

        # Save Button
        save_button = ctk.CTkButton(self.frame, text="Save", command=self.save_to_json)
        save_button.grid(row=5, column=0, columnspan=2, pady=20)

    def save_to_json(self):
        participant_name = self.participant_name_entry.get().strip()
        participant_leg = self.participant_leg_entry.get().strip()
        if participant_name and participant_leg:
            # Save to JSON
            data = {"Participant_Name": participant_name, "Participant_Leg": participant_leg}
            with open("participant_data.json", "w") as json_file:
                json.dump(data, json_file, indent=4)
            print(f"Saved: {data}")
        else:
            print("Participant's Entries are empty")
