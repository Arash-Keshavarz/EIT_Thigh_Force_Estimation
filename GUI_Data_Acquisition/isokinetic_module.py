import customtkinter as ctk
import json

class IsokineticMeasurementModule:
    def __init__(self, parent):
        
        self.frame = ctk.CTkFrame(parent)
        self.frame.grid(row=0, column=0, padx=20, pady=20)
        self.frame.grid_columnconfigure(0, weight=0)  # Label column
        self.frame.grid_columnconfigure(1, weight=1)  # Entry column

        # Create content for IsokineticMeasurementModule
        self.create_content()

    def create_content(self):
        # Title Label
        title_label = ctk.CTkLabel(self.frame, text="Isokinetic Measurement Config", font=("Arial", 18))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Participant's Name
        participant_name_label = ctk.CTkLabel(self.frame, text="Participant's Name", font=("Arial", 14))
        participant_name_label.grid(row=1, column=0, padx=5, pady=(10, 5), sticky="w")

        self.participant_name_entry = ctk.CTkEntry(self.frame, width=200, placeholder_text="Enter Name")
        self.participant_name_entry.grid(row=1, column=1, padx=5, pady=(10, 5), sticky="w")
        # Participant's Age
        participant_age_label = ctk.CTkLabel(self.frame, text="Participant's Age", font=("Arial", 14))
        participant_age_label.grid(row=2, column=0, padx=5, pady=(10, 5), sticky="w")

        self.participant_age_entry = ctk.CTkEntry(self.frame, width=200, placeholder_text="Enter Age")
        self.participant_age_entry.grid(row=2, column=1, padx=5, pady=(10, 5), sticky="w")
        
        # Participant's Gender
        participant_gender_label = ctk.CTkLabel(self.frame, text="Participant's Gender", font=("Arial", 14))
        participant_gender_label.grid(row=3, column=0, padx=5, pady=(10, 5), sticky="w")
        
        self.participant_gender_box = ctk.CTkComboBox(self.frame, values= ["male", "female"])
        self.participant_gender_box.grid(row=3, column=1, padx=5, pady=(10, 5), sticky="w")
        
        # Participant's Leg
        participant_leg_label = ctk.CTkLabel(self.frame, text="Participant's Leg", font=("Arial", 14))
        participant_leg_label.grid(row=4, column=0, padx=5, pady=(10, 5), sticky="w")

        self.participant_leg_box = ctk.CTkComboBox(self.frame, values=["right", "left"])
        self.participant_leg_box.grid(row=4, column=1, padx=5, pady=(10, 5), sticky="w")

        # Save Button
        save_button = ctk.CTkButton(self.frame, text="Save", command=self.save_to_json)
        save_button.grid(row=5, column=0, columnspan=2, pady=20)


    def save_to_json(self):

        participant_name = self.participant_name_entry.get()
        participant_age = self.participant_age_entry.get()
        participant_gender = self.participant_gender_box.get()
        participant_leg = self.participant_leg_box.get()
        if participant_name and participant_leg and participant_age and participant_gender:
            # Save the Participants information to JSON file
            data = {"Participant_Name": participant_name,
                    "Participant_Age": participant_age,
                    "Participant_Gender": participant_gender,
                    "Participant_Leg": participant_leg}
            
            with open("participant_data.json", "w") as json_file:
                json.dump(data, json_file, indent=4)
            print(f"Saved: {data}")
        else:
            print("Participant's Entries are empty")
    
    # Getter Methods
    def get_participant_name(self):
        return self.participant_name_entry.get()

    def get_participant_age(self):
        return self.participant_age_entry.get()
    
    def get_participant_gender(self):
        return self.participant_gender_box.get()
    
    def get_participant_leg(self):
        return self.participant_leg_box.get()
