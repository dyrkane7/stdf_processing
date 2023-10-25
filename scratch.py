# -*- coding: utf-8 -*-
"""
Created on Thu Apr  6 09:57:47 2023

@author: dkane
"""
# from Semi_ATE import STDF


# fp_in = "C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/partial wafer14/G4_MZMD15163_N12126.1_14_20230221.stdf"
# fp_out = "C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/partial wafer14/G4_MZMD15163_N12126.1_14_20230221.stdf"

# # Open the STDF file
# with stdf.stdf(fp_in) as f:
#     # Convert to ATDF format
#     atdf_data = f.to_atdf()

# # Write the ATDF data to a file
# with open(fp_out, "w") as f:
#     f.write(atdf_data)

from Semi_ATE import STDF
# from datetime import datetime
# from datetime import timedelta
# import tkinter as tk
# from tkinter import filedialog
import os

# root = tk.Tk()
# root.withdraw()

file_path_stdf = "C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/partial wafer14/G4_MZMD15163_N12126.1_14_20230221.stdf"
file_path_atdf = file_path_stdf.split('.stdf')[0] + '.atdf'
# print("Selected stdf file: ", file_path_stdf)
# print("Writing atdf file: ", file_path_atdf)

# dt0 = datetime.now()
# print("Start time: ", dt0)

with open(file_path_atdf, "w") as atdf:
    recs = STDF.records_from_file(file_path_stdf)
    print("converting...")
    for REC in recs:
        atdf.write(REC.to_atdf() + '\n')

# dt1 = datetime.now()
# delta = timedelta()
# delta = dt1 - dt0
# print("End time: ", dt1)
# print("Elapsed time: ", delta)