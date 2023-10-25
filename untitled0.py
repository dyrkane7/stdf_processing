# -*- coding: utf-8 -*-
"""
Created on Thu Apr  6 09:57:47 2023

@author: dkane
"""
import Semi_ATE.STDF as stdf

# Open the STDF file
with stdf.stdf("input.stdf") as f:
    # Convert to ATDF format
    atdf_data = f.to_atdf()

# Write the ATDF data to a file
with open("output.atdf", "w") as f:
    f.write(atdf_data)
