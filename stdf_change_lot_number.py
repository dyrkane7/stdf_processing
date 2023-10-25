# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 15:40:27 2023

@author: dkane
"""

from Semi_ATE.STDF import utils
from Semi_ATE.STDF import ATR

import sys
import os
import shutil
from datetime import datetime
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog

def is_datecode(string):
    if string.isnumeric() and len(string) == 8:
        if int(string[0:4]) > 2000: # if year value is greater than 2000
            if int(string[4:6]) in range(1,13): # if month value is between 1 and 12 inclusive
                if int(string[6:8]) in range(1,32): # if day of month is between 1 and 31 inclusive
                    return True
    return False  

def is_wafer_num(string):
    if len(string)==2 and string.isnumeric() and int(string) in range(1,26):
        return True
    return False

# this function updates the wafer number in the filename and file records
# and saves the original file in "old rev" directory
def stdf_change_lot_num(stdf_fp = "", new_lot_num = ""):
    if stdf_fp == "":  
        stdf_fp = filedialog.askopenfilename()
    assert os.path.isfile(stdf_fp), "the file does not exist:\n{}".format(stdf_fp)
    
    if new_lot_num == "":
        new_lot_num = input("Enter new lot number:")

    stdf_fp = os.path.abspath(stdf_fp)
    stdf_filename = os.path.basename(stdf_fp)
    stdf_dir = os.path.dirname(stdf_fp)
    
    # lot number is 2 fields behind datecode and wafer number is 1 field behind datecode in filename
    splits = os.path.splitext(stdf_filename)[0].split('_')
    found_match = False
    for i, split in enumerate(splits):
        if is_datecode(split) and is_wafer_num(splits[i-1]):
            splits[i-2] = new_lot_num
            found_match = True
    assert found_match, f"could not find lot number in filename: {stdf_filename}"
    
    new_prim_lot_num = new_lot_num.split('.')[0]
    new_sub_lot_num = new_lot_num.split('.')[1]
    new_fp = stdf_dir + "\\" + "_".join(splits) + ".stdf"
    new_fp = os.path.abspath(new_fp)
    print("new file:", new_fp)
    assert not os.path.isfile(new_fp), "the file already exists:\n{}".format(new_fp)
    
    endian, version = utils.endian_and_version_from_file(stdf_fp)
    id_ts_dict = utils.id_to_ts()
    # get old lot number
    for rec in utils.check_records_from_file(stdf_fp):
        _, rec_type, rec_sub, raw_bytes = rec
        if (rec_type,rec_sub) == id_ts_dict["MIR"]:
            rec_obj = utils.create_record_object(version, endian, "MIR", raw_bytes)
            # MRR LOT_ID has format: {MAIN_LOT_ID}.{SUBLOT_ID}_{PART_NUM}
            temp = rec_obj.get_fields("LOT_ID")[3]
            old_prim_lot_num = temp.split('.')[0]
            old_sub_lot_num = temp.split('.')[1].split('_')[0]
            old_die_part_num = temp.split('.')[1].split('_')[1]
            print("old_sub_lot_num:", old_sub_lot_num)
            print("old_prim_lot_num:", old_prim_lot_num)
            print("old_die_part_num:", old_die_part_num)
    
    with open(new_fp, 'wb') as new_stdf:
        for rec in utils.check_records_from_file(stdf_fp):
            insert_atr_flag = False
            _, rec_type, rec_sub, raw_bytes = rec
            if (rec_type,rec_sub) == id_ts_dict["FAR"]:
                insert_atr_flag = True
            if (rec_type,rec_sub) == id_ts_dict["MIR"]:
                rec_obj = utils.create_record_object(version, endian, "MIR", raw_bytes)
                print(rec_obj)
                # MRR LOT_ID has format: {MAIN_LOT_ID}.{SUBLOT_ID}_{PART_NUM}
                
                print("new_sub_lot_num:", new_sub_lot_num)
                print("new_prim_lot_num:", new_prim_lot_num)
                new_wrr_lot_num = new_prim_lot_num + "." + new_sub_lot_num + "_" + old_die_part_num
                rec_obj.set_value("LOT_ID", new_wrr_lot_num)
                rec_obj.set_value("SBLOT_ID", new_sub_lot_num)
                raw_bytes = rec_obj.__repr__()
                print(rec_obj)
            new_stdf.write(raw_bytes)
            if insert_atr_flag:
                rec_obj = ATR(version=version, endian=endian)
                dt = datetime.now()
                program_info = os.path.basename(__file__) + \
                    ", old_lot_num: " + old_prim_lot_num + "." + old_sub_lot_num + \
                    ", new_lot_num: " + new_prim_lot_num + "." + new_sub_lot_num
                rec_obj.set_value("MOD_TIM", int(dt.timestamp()))
                rec_obj.set_value("CMD_LINE", program_info)
                print(rec_obj)
                raw_bytes = rec_obj.__repr__()
                # print("rec length:", rec_obj.get_value("REC_LEN"))
                new_stdf.write(raw_bytes)
    
    # save original file under new name
    old_rev_dir = stdf_dir + "\\old stdf rev\\"
    if not os.path.isdir(old_rev_dir):
        os.mkdir(old_rev_dir)
    rev = 1
    old_rev_filename = os.path.splitext(stdf_filename)[0] + "_WRONG_LOT_NUM{}.stdf".format(rev)
    while os.path.isfile(old_rev_dir + old_rev_filename):
        rev += 1
        old_rev_filename = os.path.splitext(stdf_filename)[0] + "_WRONG_LOT_NUM{}.stdf".format(rev)
    print("old rev filepath:", old_rev_dir + old_rev_filename)
    shutil.move(stdf_fp, old_rev_dir + old_rev_filename)

if __name__ == '__main__':
    fp = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/XR800G/N13222.2/phase 2/XR87275133_13222.2_08_20230404.stdf"
    stdf_change_lot_num(fp, new_lot_num="N13222.2")
    # stdf_change_wafer_num()
