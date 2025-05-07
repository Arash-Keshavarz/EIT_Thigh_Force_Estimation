# EIT Thigh Force Estimation

## Abstract

Assessing muscle strength and estimating muscle force during everyday activities plays a crucial role in understanding human movement, rehabilitation, and sports science.  
This project leverages **Electrical Impedance Tomography (EIT)** — a non-invasive imaging technique that captures the internal conductivity distribution of tissues — to explore the feasibility of **force level estimation** from EIT data.

Inspired by *EITPose*[^1], which demonstrated real-time monitoring of forearm muscle activity using EIT, we extend this approach to the thigh region.  
A custom-built belt equipped with 16 electrodes was developed to record EIT data, while an Isoforce device simultaneously captured torque measurements.

The study is structured in two phases:
- Estimation of discrete force levels (20–80 Nm) across multiple participants.
- Continuous torque estimation, formulated as a regression problem.

---

## Table of Contents

- [Data Quality Check](#data-quality-check)
- [Data Preprocessing and Synchronization](#data-preprocessing-and-synchronization)
- [Dataset Generation](#dataset-generation)
- [PCA Analysis](notebooks/3.PCA_Analysis.ipynb)
- [Classification](#classification)
- [Regression](#regression)
- [Outlook](#outlook)
- [Installation](#installation)
- [Author](#author)
- [Acknowledgements](#acknowledgements)

---

## Data Quality Check

*(Coming soon.)*

## Data Preprocessing and Synchronization

*(Coming soon.)*

## Dataset Generation

*(Coming soon.)*


## Classification

*(Coming soon.)*

## Regression

*(Coming soon.)*

## Outlook

*(Coming soon.)*

---

## Installation

Make sure you have **Python 3.8** or later installed.  
Clone the repository and install the required packages:

```bash
git clone https://github.com/Arash-Keshavarz/EIT_Thigh_Force_Estimation.git
cd EIT_Thigh_Force_Estimation
pip install -r requirements.txt
```

---

## Author

This repository was created and is maintained by Arash Keshavarz,
Institute of Communications Engineering, University of Rostock, Germany.

Contact: arashkeshavarzx@gmail.com

---

## Acknowledgements

- The EITPose project served as an inspiration for extending EIT applications to the thigh region.
- Special thanks to the Institute of Communications Engineering, University of Rostock, for their support.
