import os
import sys
import argparse
sys.path.append("/Users/MA_Arash/MA_git/EIT_Thigh_Force_Estimation")

from eit_utils import *
from src.toolbox import Protocol


parser = argparse.ArgumentParser(description="Process EIT data directory.")
parser.add_argument("--base_dir", type=str, required=True, help="Base directory containing participant folders")
args = parser.parse_args()

base_dir = args.base_dir

# Automatically process all P01 - P15 folders
participants = [f"P{p:02d}" for p in range(1, 16)]  # Generates P01, P02, ..., P15

for participant in participants:
    file_path = os.path.join(base_dir, participant)
    
    if os.path.exists(file_path):  # Check if the folder exists
        print(f"Processing: {file_path}")
        protocol = Protocol(file_path)
        convert_eit_directory_to_npz(file_path, protocol)
    else:
        print(f"Skipping {file_path}, folder does not exist.")

print("Conversion completed!")