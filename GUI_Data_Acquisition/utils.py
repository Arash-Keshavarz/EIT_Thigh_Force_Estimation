import os
from datetime import datetime
from fpdf import FPDF, XPos, YPos
from typing import List, Optional, Dict


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



class ExperimentProtocol:
    """
    A class to generate an experiment protocol PDF.

    Attributes:
        title (str): The title of the experiment.
        experimenter (str): The name of the experimenter.
        date (str): The date of the experiment (default: current datetime).
        sections (List[Dict[str, str]]): A list of sections, each containing a heading and content.
    """

    def __init__(self, title: str, experimenter: str, date: Optional[str] = None) -> None:
        """
        Initializes the ExperimentProtocol with title, experimenter, and optional date.

        Args:
            title (str): The title of the experiment.
            experimenter (str): The name of the experimenter.
            date (Optional[str]): The date of the experiment (default: current date and time).
        """
        self.title = title
        self.experimenter = experimenter
        self.date = date if date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.sections: List[Dict[str, str]] = []

    def add_section(self, heading: str, content: str) -> None:
        """
        Adds a section to the experiment protocol.

        Args:
            heading (str): The section title.
            content (str): The section content.
        """
        if not heading or not content:
            raise ValueError("Both heading and content must be provided.")
        self.sections.append({"heading": heading, "content": content})

    def _add_experiment_details(self, pdf: FPDF) -> None:
        """Adds experiment metadata (title, experimenter, date) to the PDF."""
        pdf.set_font("Times", style="B", size=16)
        pdf.cell(0, 10, self.title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(10)

        pdf.set_font("Times", size=12)
        pdf.cell(0, 10, f"Experimenter: {self.experimenter}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 10, f"Date: {self.date}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(10)

    def _add_sections(self, pdf: FPDF) -> None:
        """Adds all sections to the PDF."""
        for section in self.sections:
            pdf.set_font("Times", style="B", size=14)
            pdf.cell(0, 10, section["heading"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)

            pdf.set_font("Times", size=12)
            pdf.multi_cell(0, 10, section["content"])
            pdf.ln(5)

    def generate_pdf(self, filename: str) -> None:
        """
        Generates and saves the experiment protocol as a PDF file.

        Args:
            filename (str): The name of the output PDF file.
        """
        if not filename.lower().endswith(".pdf"):
            raise ValueError("Filename must have a .pdf extension.")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        self._add_experiment_details(pdf)
        self._add_sections(pdf)

        try:
            pdf.output(filename)
            print(f"PDF successfully saved as '{filename}'!")
        except Exception as e:
            print(f"Error saving PDF: {e}")
