# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 18:38:47 2023

@author: dkane
"""
from Semi_ATE.STDF import utils
from Semi_ATE.STDF import ATR

import os
import shutil
from datetime import datetime
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog

# this function updates the wafer number in the filename and file records
# and saves the original file in "old rev" directory
def stdf_change_wafer_num(stdf_fp = ""):
    if stdf_fp == "":  
        stdf_fp = filedialog.askopenfilename()
    assert os.path.isfile(stdf_fp), "the file does not exist:\n{}".format(stdf_fp)
        
    new_wafer_num = input("Enter new wafer number:")
    assert new_wafer_num.isnumeric(), "new wafer number must be numeric"
    assert int(new_wafer_num) <= 25, "new wafer number must be less than 25"
    new_wafer_num = new_wafer_num.zfill(2)

    stdf_fp = os.path.abspath(stdf_fp)
    stdf_filename = os.path.basename(stdf_fp)
    stdf_dir = os.path.dirname(stdf_fp)
    
    splits = stdf_filename.split('_')
    old_wafer_num = splits[3]
    splits[3] = new_wafer_num
    new_fp = stdf_dir + "\\" + "_".join(splits)
    new_fp = os.path.abspath(new_fp)
    print("new file:", new_fp)
    assert not os.path.isfile(new_fp), "the file already exists:\n{}".format(new_fp)
    
    new_stdf = open(new_fp, 'wb')
    
    endian, version = utils.endian_and_version_from_file(stdf_fp)
    id_ts_dict = utils.id_to_ts()
    for rec in utils.check_records_from_file(stdf_fp):
        insert_atr_flag = False
        _, rec_type, rec_sub, raw_bytes = rec
        if (rec_type,rec_sub) == id_ts_dict["FAR"]:
            insert_atr_flag = True
        if (rec_type,rec_sub) == id_ts_dict["WIR"]:
            rec_obj = utils.create_record_object(version, endian, "WIR", raw_bytes)
            rec_obj.set_value("WAFER_ID", new_wafer_num)
            raw_bytes = rec_obj.__repr__()
            # print(rec_obj)
        if (rec_type,rec_sub) == id_ts_dict["WRR"]:
            rec_obj = utils.create_record_object(version, endian, "WRR", raw_bytes)
            rec_obj.set_value("WAFER_ID", new_wafer_num)
            raw_bytes = rec_obj.__repr__()
            # print(rec_obj)
        new_stdf.write(raw_bytes)
        if insert_atr_flag:
            rec_obj = ATR(version=version, endian=endian)
            dt = datetime.now()
            program_info = os.path.basename(__file__) + ", old_wafer_number: " + old_wafer_num + ", new_wafer_num: " + new_wafer_num
            rec_obj.set_value("MOD_TIM", int(dt.timestamp()))
            rec_obj.set_value("CMD_LINE", program_info)
            raw_bytes = rec_obj.__repr__()
            # print("rec length:", rec_obj.get_value("REC_LEN"))
            new_stdf.write(raw_bytes)
    new_stdf.close()
    
    # save original file under new name
    old_rev_dir = stdf_dir + "\\old stdf rev\\"
    if not os.path.isdir(old_rev_dir):
        os.mkdir(old_rev_dir)
    rev = 1
    old_rev_filename = os.path.splitext(stdf_filename)[0] + "_WRONG_WAFER_NUM{}.stdf".format(rev)
    while os.path.isfile(old_rev_dir + old_rev_filename):
        rev += 1
        old_rev_filename = os.path.splitext(stdf_filename)[0] + "_WRONG_WAFER_NUM{}.stdf".format(rev)
    print("old rev filepath:", old_rev_dir + old_rev_filename)
    shutil.move(stdf_fp, old_rev_dir + old_rev_filename)

if __name__ == '__main__':
    fp = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_05_20230213.stdf"
    stdf_change_wafer_num(fp)
    # stdf_change_wafer_num()