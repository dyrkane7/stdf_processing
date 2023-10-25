# -*- coding: utf-8 -*-
"""
Created on Sun Jan  8 19:31:33 2023

@author: dkane
"""

from Semi_ATE.STDF import utils

import os
from datetime import datetime
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog
     
def stdf_remove_invalid_bin_num(stdf_fp = ""):
    if stdf_fp == "":  
        stdf_fp = filedialog.askopenfilename()
        
    dt0 = datetime.now()
    print("Start time: ", dt0)
    
    stdf_fp = os.path.abspath(stdf_fp)
    stdf_filename = os.path.basename(stdf_fp)
    stdf_dir = os.path.dirname(stdf_fp)
    print("stdf file name:", stdf_filename)
    print("stdf directory:", stdf_dir)
    
    assert os.path.isfile(stdf_fp), "the file does not exist:\n{}".format(stdf_fp)
    assert utils.is_STDF(stdf_fp), "the file is not stdf file:\n{}".format(stdf_fp)
    endian, version = utils.endian_and_version_from_file(stdf_fp)
    
    new_stdf = open(stdf_fp + '_', 'wb')
    
    part_count = 0
    invalid_part_i = []
    id_ts_dict = utils.id_to_ts()
    # TODO: timing test with and without enumerate() statement
    for i, rec in enumerate(utils.check_records_from_file(stdf_fp)):
        _, rec_type, rec_sub, raw_bytes = rec
        if (rec_type,rec_sub) == id_ts_dict["PIR"]:
            rec_obj = utils.create_record_object(version, endian, "PIR", raw_bytes)
            part_count += 1
        elif (rec_type,rec_sub) == id_ts_dict["PRR"]:
            rec_obj = utils.create_record_object(version, endian, "PRR", raw_bytes)
            x = rec_obj.get_fields('X_COORD')[3]
            y = rec_obj.get_fields('Y_COORD')[3]
            hbin = rec_obj.get_fields('HARD_BIN')[3]
            sbin = rec_obj.get_fields('SOFT_BIN')[3]
            if sbin == 65535 and hbin == 65535:
                invalid_part_i.append(part_count)
                print("Found Invalid part result:", "x:", x, "y:", y,"hbin:", hbin, "sbin:", sbin, "part count:", part_count)
        elif (rec_type,rec_sub) == id_ts_dict["SBR"]:
            rec_obj = utils.create_record_object(version, endian, "SBR", raw_bytes)
            if rec_obj.get_fields('SBIN_NUM')[3] == 65535:
                print("FOUND INVALID SBIN 65535")
        elif (rec_type,rec_sub) == id_ts_dict["HBR"]:
            rec_obj = utils.create_record_object(version, endian, "HBR", raw_bytes)
            if rec_obj.get_fields('HBIN_NUM')[3] == 65535:
                print("FOUND INVALID HBIN 65535")
    print('invalid_part_i:', invalid_part_i)
    n_prr = part_count
    print(n_prr)
    part_count = 0
    for i, rec in enumerate(utils.check_records_from_file(stdf_fp)):
        _, rec_type, rec_sub, raw_bytes = rec
        write_rec = True
        if (rec_type,rec_sub) == id_ts_dict["PIR"]:
            part_count += 1
        elif (rec_type,rec_sub) == id_ts_dict["HBR"]:
            rec_obj = utils.create_record_object(version, endian, "HBR", raw_bytes)
            if rec_obj.get_fields('HBIN_NUM')[3] == 65535:
                write_rec = False
        elif (rec_type,rec_sub) == id_ts_dict["SBR"]:
            rec_obj = utils.create_record_object(version, endian, "SBR", raw_bytes)
            if rec_obj.get_fields('SBIN_NUM')[3] == 65535:
                write_rec = False
        if (part_count not in invalid_part_i) and write_rec:
            new_stdf.write(raw_bytes)
        if (rec_type,rec_sub) == id_ts_dict["PRR"]:
            if part_count == n_prr:
                part_count = 0
            
    new_stdf.close()
    dt1 = datetime.now()
    delta = timedelta()
    delta = dt1 - dt0
    print("\nEnd time: ", dt1)
    print("Elapsed time: ", delta)

if __name__ == '__main__':
    fp = r"C:\Users\dkane\OneDrive - Presto Engineering\Documents\Infinera\Gen 4\N12126.1\stdf\TIA\G4_TIA25133_N12126.1_15_20230110.stdf_"
    # stdf_remove_invalid_bin_num(fp)
    stdf_remove_invalid_bin_num()