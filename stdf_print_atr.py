# -*- coding: utf-8 -*-
"""
Created on Sun Feb 19 16:12:15 2023

@author: dkane
"""
from Semi_ATE.STDF import utils

import os
from datetime import datetime
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog

def stdf_print_atr(stdf_fp = ""):
    if stdf_fp == "":  
        stdf_fp = filedialog.askopenfilename()
    assert os.path.isfile(stdf_fp), "the file does not exist:\n{}".format(stdf_fp)

    stdf_fp = os.path.abspath(stdf_fp)
    print("stdf filepath:", stdf_fp)
    
    endian, version = utils.endian_and_version_from_file(stdf_fp)
    id_ts_dict = utils.id_to_ts()
    for rec in utils.check_records_from_file(stdf_fp):
        _, rec_type, rec_sub, raw_bytes = rec
        if (rec_type,rec_sub) == id_ts_dict["ATR"]:
            rec_obj = utils.create_record_object(version, endian, "ATR", raw_bytes)
            print(rec_obj)

if __name__ == '__main__':
    fp = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/partial wafer14/G4_MZMD15163_N12126.1_14_20230307.stdf"
    # fp = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_01_20221128.stdf"
    stdf_print_atr(fp)
    # stdf_print_atr()
