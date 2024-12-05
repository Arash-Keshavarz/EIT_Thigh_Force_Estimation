import customtkinter as ctk
import json

class IsokineticMeasurementModule:
    
    def __init__(self, parent):
        
        self.frame = ctk.CTkFrame(parent, width= 700)
        self.frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsw")
        
        ################################
        # create content for IsokineticMeasurementModule
        self.create_content()
        
    def create_content(self):
        title_label = ctk.CTkLabel(self.frame, text="IsoKinetic Measurement Config", font=("Arial", 18))
        title_label.pack(pady=10)
        
        # Participants Name
        participant_name = ctk.CTkLabel(self.frame, text="Participant's Name: ", font=("Arial", 14))
        participant_name.pack(pady=(10, 0))
        
        self.participant_name_entry = ctk.CTkEntry(self.frame, width=300, placeholder_text = "Enter Name") 
        self.participant_name_entry.pack(pady=(5, 20))
        
        participant_leg = ctk.CTkLabel(self.frame, text="Participant's Leg: ", font=("Arial",14))
        participant_leg.pack(pady=(10, 0))
        
        self.participant_leg_entry = ctk.CTkEntry(self.frame, width=300, placeholder_text = "Enter Leg")
        self.participant_leg_entry.pack(pady=(5, 20))
        
        ################################
        # Button for Save
        save_button = ctk.CTkButton(self.frame, text="Save", command= self.save_to_json)
        save_button.pack(pady=10)
        
    def save_to_json(self):
        
        participant_name = self.participant_name_entry.get().strip()
        participant_leg = self.participant_leg_entry.get().strip()
        if participant_name and participant_leg:
            # Save to JSON
            data = {"Participant_Name" : participant_name,
                    "Participant_Leg" : participant_leg}
            with open("participant_data.json", "w") as json_file:
                json.dump(data, json_file, indent=4)
            print(f"Saved: {data}")
        else:
            print("Participant's Entries are empty")
                
            