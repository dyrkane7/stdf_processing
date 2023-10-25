# -*- coding: utf-8 -*-
"""
Created on Fri Sep 23 20:44:05 2022

@author: dkane
"""

from Semi_ATE import STDF
from datetime import datetime
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog
import os

def stdf_to_atdf(fp_list = [], debug = False):
    root = tk.Tk()
    root.withdraw()
    
    if not fp_list:
        fp_list = filedialog.askopenfilenames()
        
    for stdf_fp in fp_list:
        fp_wo_ext, ext = os.path.splitext(stdf_fp)
        
        atdf_fp = fp_wo_ext + '.atdf'
        
        if debug:
            print("Selected stdf file: ", stdf_fp)
            print("Writing atdf file: ", atdf_fp)
        
        dt0 = datetime.now()
        
        if debug:
            print("Start time: ", dt0)
        
        with open(atdf_fp, "w") as atdf:
            recs = STDF.records_from_file(stdf_fp)
            print("generating ATDF...")
            for REC in recs:
                atdf.write(REC.to_atdf() + '\n')
        
        dt1 = datetime.now()
        delta = timedelta()
        delta = dt1 - dt0
        
        if debug:
            print("End time: ", dt1)
            print("Elapsed time: ", delta)
        
if __name__ == "__main__":
    fp_list = []
    
    stdf_to_atdf(debug=True)
    # stdf_to_atdf(fp_list)


