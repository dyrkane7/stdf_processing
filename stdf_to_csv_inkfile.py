# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 21:47:41 2023

@author: dkane
"""

# This program is specific to Infinera wafer sort stdf files

# This program assumes first pass all dies tested and 2nd pass fail dies tested

# WARNING: Inkfile name must be less than 43 characters
# Inking program can read only 43 characters

from Semi_ATE.STDF import utils

import csv
import os
from datetime import datetime
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog

def dev_and_pn_from_filename(stdf_filename):
    splits = stdf_filename.split('_')
    die_part = splits[1][-3:]
    device = splits[0]
    print("die part:", die_part, "device:", device)
    return device, die_part

# def get_good_bin_list(stdf_filename):
#     device, die_part = dev_and_pn_from_filename(stdf_filename)
#     if device == "G6" and die_part == "131": # Gen6 fully optimized
#         return [1,2]
#     elif device in ["G6", "G4"] and die_part in ["117", "163", "133"]: # Gen6 partially optimized
#         return [1]
#     raise Exception("die part ({}) or device name ({}) not recognized.".format(die_part, device))

# def get_inkfile_name(stdf_filename):
#     device, die_part = dev_and_pn_from_filename(stdf_filename)
#     if device == "G6" and die_part == "131": # Gen6 fully optimized
#         return [1,2]
#     elif device == "G6" and die_part == "117": # Gen6 partially optimized
#         return [1]
#     elif device == "G4" and die_part == "163": # Gen4 MZMD
#         return [1]
#     elif device == "G4" and die_part == "133": # Gen6 TIA
#         return [1]
#     raise Exception("die part ({}) or device name ({}) not recognized.".format(die_part, device))

def stdf_to_csv_infkfile(stdf_fp):
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
    
    device, die_part = dev_and_pn_from_filename(stdf_filename)
    stdf_fileroot = os.path.splitext(stdf_filename)[0]
    splits = stdf_fileroot.split('_')
    csv_filename = "_".join(splits[:4]) + "_inkfile.csv"
    print("csv_filename:", csv_filename)
    if device == "G6" and die_part == "131": # Gen6 fully optimized
        good_bins = [1,2]
        csv_filename = "G6_NEW" + csv_filename.split('G6', 1)[1]
    elif device == "G6" and die_part == "117": # Gen6 partially optimized
        good_bins = [1]
        csv_filename = "G6_OLD" + csv_filename.split('G6', 1)[1]
    elif device == 'G4' and die_part in ["163", "133"]: # Gen4 TIA or MZMD
        good_bins = [1]
    else:
        raise Exception("die part ({}) or device name ({}) not recognized.".format(die_part, device))
        
    print("csv_filename:", csv_filename)
    csv_fp = stdf_dir + '\\' + csv_filename
    
    die_info = {}
    id_ts_dict = utils.id_to_ts()
    n_kgd = 0
    for rec in utils.check_records_from_file(stdf_fp):
        _, rec_type, rec_sub, raw_bytes = rec
        if (rec_type,rec_sub) == id_ts_dict["PRR"]:
            rec_obj = utils.create_record_object(version, endian, "PRR", raw_bytes)
            x = rec_obj.get_fields('X_COORD')[3]
            y = rec_obj.get_fields('Y_COORD')[3]
            soft_bin = rec_obj.get_fields('SOFT_BIN')[3]
            die_info[(x,y)] = soft_bin


    sorted_coor = sorted(die_info.keys())
    print(good_bins)
    with open(csv_fp, 'w', newline = '') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["RETX","RETY","DIE","NDIE","BIN"])
        for x, y in sorted_coor:
            if die_info[(x,y)] in good_bins:
                n_kgd += 1
                ink_bin_code = 1
            else:
                ink_bin_code = 99
            writer.writerow([x,y,1,1,ink_bin_code])
        writer.writerow(["","","","","KGD = {}".format(n_kgd)])
    
    # open file in excel
    # add quotes around any directory name with spaces, or system command wont work
    splits = csv_fp.split('\\')
    tmp = ""
    for split in splits:
        if  (' ' in split) == True:
            split = ('"' + split + '"')
        tmp += (split + "\\")
    csv_fp = tmp[0:-1]
    os.system(csv_fp)
    
    dt1 = datetime.now()
    delta = timedelta()
    delta = dt1 - dt0
    print("\nEnd time: ", dt1)
    print("Elapsed time: ", delta)

if __name__ == '__main__':
    # fp = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 6/M99546.1/stdf/G6_XCVR6775131_M99546.1_01_20220714.stdf"
    fp_list = filedialog.askopenfilenames()
    for fp in fp_list:
        stdf_to_csv_infkfile(fp)