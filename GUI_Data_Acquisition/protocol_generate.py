from datetime import datetime

from fpdf import FPDF, XPos, YPos


class ExperimentProtocol:
    def __init__(self, title, experimenter, date=None):
        self.title = title
        self.experimenter = experimenter
        self.date = date if date else datetime.now().strftime("%Y-%m-%d")
        self.sections = []

    def add_section(self, heading, content):
        self.sections.append({"heading": heading, "content": content})

    def generate_pdf(self, filename):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Times", size=12)

        # Title
        pdf.set_font("Times", style="B", size=16)
        pdf.cell(0, 10, self.title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(10)

        # Experiment details
        pdf.set_font("Times", size=12)
        pdf.cell(
            0,
            10,
            f"Experimenter: {self.experimenter}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.cell(0, 10, f"Date: {self.date}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(10)

        # Sections
        for section in self.sections:
            pdf.set_font("Times", style="B", size=14)
            pdf.cell(0, 10, section["heading"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)
            pdf.set_font("Times", size=12)
            pdf.multi_cell(0, 10, section["content"])
            pdf.ln(5)

        # Save
        pdf.output(filename)
        print(f"PDF successfully saved as '{filename}'!")