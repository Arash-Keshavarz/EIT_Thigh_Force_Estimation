import os

def create_participant_directory(participant_num: str) -> tuple[str, str]:
    """
    Creates a structured directory for each participant within the 'measurements' folder.
    
    This function ensures the existence of:
    - A participant-specific directory inside 'measurements'.
    - Two subdirectories: 'eit_raw' and 'iso_raw'.
    
    Parameters:
        participant_name (str): The name or identifier of the participant.

    Returns:
        tuple[str, str]: Paths to the 'eit_raw' and 'iso_raw' directories.
    """
    base_dir = "Final_Measurements"
    participant_dir = os.path.join(base_dir, participant_num)
    
    # Create ISO and EIT subdirectories #
    for sub_dir in ["", "eit_raw", "iso_raw"]:
        os.makedirs(os.path.join(participant_dir, sub_dir), exist_ok=True)
    
    return os.path.join(participant_dir, "eit_raw"), os.path.join(participant_dir, "iso_raw")

