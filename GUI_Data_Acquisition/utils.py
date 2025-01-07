import os

def create_participant_directory(participant_name):
    """
    Create a directory structure for storing participant data.
    """
    # Define the base directory

    base_dir = "measurements"

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    # Define the participant's directory path
    participant_dir = os.path.join(base_dir, participant_name)
    
    if not os.path.exists(participant_dir):
        os.makedirs(participant_dir)

    return participant_dir