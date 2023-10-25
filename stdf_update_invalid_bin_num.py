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

'''
If part test crashes or exits without assigning bin#
part result record gets assigned SW/HW bin# 65535.
This bin# is considered invalid by some stdf readers and can cause loading errors. 

This script updates PRR SW/HW bin# to a new value for all bin 65535 parts
'''

def stdf_update_invalid_bin_num(hw_bin_num, sw_bin_num, hw_bin_nam, sw_bin_nam, stdf_fp = ""):
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
        
    id_ts_dict = utils.id_to_ts()
    with open(stdf_fp + '_', 'wb') as new_stdf:
        # invalid_sw_bin_count = 0
        for i, rec in enumerate(utils.check_records_from_file(stdf_fp)):
            _, rec_type, rec_sub, raw_bytes = rec
            if (rec_type,rec_sub) == id_ts_dict["PRR"]:
                rec_obj = utils.create_record_object(version, endian, "PRR", raw_bytes)
                x = rec_obj.get_fields('X_COORD')[3]
                y = rec_obj.get_fields('Y_COORD')[3]
                hbin = rec_obj.get_fields('HARD_BIN')[3]
                sbin = rec_obj.get_fields('SOFT_BIN')[3]
                if sbin == 65535:
                    rec_obj.set_value("SOFT_BIN", sw_bin_num)
                    raw_bytes = rec_obj.__repr__()
                    print("Found Invalid HW bin:", "x:", x, "y:", y,"sbin:", sbin)
                if hbin == 65535:
                    rec_obj.set_value("HARD_BIN", hw_bin_num)
                    raw_bytes = rec_obj.__repr__()
                    print("Found Invalid SW bin:", "x:", x, "y:", y,"hbin:", hbin)
            elif (rec_type,rec_sub) == id_ts_dict["HBR"]:
                rec_obj = utils.create_record_object(version, endian, "HBR", raw_bytes)
                if rec_obj.get_fields('HBIN_NUM')[3] == 65535:
                    rec_obj.set_value("HBIN_NAM", hw_bin_nam)
                    rec_obj.set_value("HBIN_NUM", hw_bin_num)
                    raw_bytes = rec_obj.__repr__()
            elif (rec_type,rec_sub) == id_ts_dict["SBR"]:
                rec_obj = utils.create_record_object(version, endian, "SBR", raw_bytes)
                if rec_obj.get_fields('SBIN_NUM')[3] == 65535:
                    rec_obj.set_value("SBIN_NAM", sw_bin_nam)
                    rec_obj.set_value("SBIN_NUM", sw_bin_num)
                    raw_bytes = rec_obj.__repr__()
            new_stdf.write(raw_bytes)
            
    dt1 = datetime.now()
    delta = timedelta()
    delta = dt1 - dt0
    print("\nEnd time: ", dt1)
    print("Elapsed time: ", delta)

if __name__ == '__main__':
    fp = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/XR400G/N11163.1\XR47075166_N11163.1_09_20230503.stdf"
    stdf_update_invalid_bin_num(
        hw_bin_num=26, sw_bin_num=26330, 
        hw_bin_nam="TiaVtiaDacTiaDLVrefTiaPDPMCalTiaOffLoopRange", 
        sw_bin_nam = "TiaPDPMTiaScreenVoutDelta", 
        stdf_fp = fp)
    # stdf_update_invalid_bin_num()