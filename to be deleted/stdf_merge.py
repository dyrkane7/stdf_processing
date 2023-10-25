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
     
def init_bin_counts(fp, sw_bin_cnts, hw_bin_cnts):
    endian, version = utils.endian_and_version_from_file(fp)
    id_ts_dict = utils.id_to_ts()
    for rec in utils.check_records_from_file(fp):
        _, rec_type, rec_sub, raw_bytes = rec
        if (rec_type,rec_sub) == id_ts_dict["SBR"]:
            rec_obj = utils.create_record_object(version, endian, "SBR", raw_bytes)
            sw_bin_cnts[rec_obj.get_fields('SBIN_NUM')[3]] = 0 # initialize SW bin count dict entry
        elif (rec_type,rec_sub) == id_ts_dict["HBR"]:
            rec_obj = utils.create_record_object(version, endian, "HBR", raw_bytes)
            hw_bin_cnts[rec_obj.get_fields('HBIN_NUM')[3]] = 0 # initialize HW bin count dict entry
    return sw_bin_cnts, hw_bin_cnts

def add_prrs_to_wmap(fp, wmap, rtst_cnt):
    endian, version = utils.endian_and_version_from_file(fp)
    id_ts_dict = utils.id_to_ts()
    for i, rec in enumerate(utils.check_records_from_file(fp)):
        _, rec_type, rec_sub, raw_bytes = rec
        if (rec_type,rec_sub) == id_ts_dict["PRR"]:
            rec_obj = utils.create_record_object(version, endian, "PRR", raw_bytes)
            # part_flag = rec_obj.get_fields('PART_FLG')[3]
            x = rec_obj.get_fields('X_COORD')[3]
            y = rec_obj.get_fields('Y_COORD')[3]
            hw_bin = rec_obj.get_fields('HARD_BIN')[3]
            sw_bin = rec_obj.get_fields('SOFT_BIN')[3]
            if (x,y) in wmap and wmap[(x,y)] != 1:
                rtst_cnt += 1
                wmap[(x,y)] = {"hw_bin": hw_bin, "sw_bin": sw_bin}
            else:
                wmap[(x,y)] = {"hw_bin": hw_bin, "sw_bin": sw_bin}
    return wmap, rtst_cnt
            
# stdf file #1 is first pass
# stdf file #2 is second pass

# updates PCR (PART_CNT, RTST_CNT, GOOD_CNT)
# updates WRR (PART_CNT, RTST_CNT, GOOD_CNT)
# updates HBR and SBR (HBIN_CNT / SBIN_CNT)
def stdf_merge(stdf_fp1 = "", stdf_fp2 = ""):
    if stdf_fp1 == "":  
        stdf_fp1 = filedialog.askopenfilename()
    if stdf_fp2 == "":  
        stdf_fp2 = filedialog.askopenfilename()
        
    dt0 = datetime.now()
    print("Start time: ", dt0)
    
    stdf_fp1 = os.path.abspath(stdf_fp1)
    stdf_filename1 = os.path.basename(stdf_fp1)
    stdf_dir1 = os.path.dirname(stdf_fp1)
    print("stdf file name 1:", stdf_filename1)
    print("stdf directory 1:", stdf_dir1)
    
    assert os.path.isfile(stdf_fp1), "the file1 does not exist:\n{}".format(stdf_fp1)
    assert utils.is_STDF(stdf_fp1), "the file1 is not stdf file:\n{}".format(stdf_fp1)
    endian1, version1 = utils.endian_and_version_from_file(stdf_fp1)
    
    stdf_fp2 = os.path.abspath(stdf_fp2)
    stdf_filename2 = os.path.basename(stdf_fp2)
    stdf_dir2 = os.path.dirname(stdf_fp2)
    print("stdf file name 2:", stdf_filename2)
    print("stdf directory 2:", stdf_dir2)
    
    assert os.path.isfile(stdf_fp2), "the file 2 does not exist:\n{}".format(stdf_fp2)
    assert utils.is_STDF(stdf_fp2), "the file 2 is not stdf file:\n{}".format(stdf_fp2)
    endian2, version2 = utils.endian_and_version_from_file(stdf_fp2)
    
    sw_bin_cnts = {}
    hw_bin_cnts = {}
    good_cnt, rtst_cnt, part_cnt = 0, 0, 0
    wmap = {}
    
    sw_bin_cnts, hw_bin_cnts = init_bin_counts(stdf_fp1, sw_bin_cnts, hw_bin_cnts)
    sw_bin_cnts, hw_bin_cnts = init_bin_counts(stdf_fp2, sw_bin_cnts, hw_bin_cnts)
    
    wmap, rtst_cnt = add_prrs_to_wmap(stdf_fp1, wmap, rtst_cnt) # Build partial wafer map with PRR's from stdf file #1
    wmap, rtst_cnt = add_prrs_to_wmap(stdf_fp2, wmap, rtst_cnt) # Complete wafer map with PRR's from stdf file #2

    for (x,y) in wmap:
        part_cnt += 1
        sw_bin_cnts[wmap[(x,y)]["sw_bin"]] += 1
        hw_bin_cnts[wmap[(x,y)]["hw_bin"]] += 1
        if wmap[(x,y)]["sw_bin"] == 1:
            good_cnt += 1
    
    print("good_cnt:", good_cnt)
    print("rtst_cnt:", rtst_cnt)
    print("part_cnt:", part_cnt)
    print("sw_bin_cnts:", sw_bin_cnts)
    print("hw_bin_cnts:", hw_bin_cnts)
    # print("wmap:", wmap)
    # id_ts_dict = utils.id_to_ts()        

    # new_stdf = open(stdf_fp1 + '_', 'wb')
    # new_stdf.close()
    dt1 = datetime.now()
    delta = timedelta()
    delta = dt1 - dt0
    print("\nEnd time: ", dt1)
    print("Elapsed time: ", delta)

if __name__ == '__main__':
    fp1 = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/M88855.1/stdf/G4_MZMD15163_M88855.1_22_20230118.stdf"
    fp2 = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/M88855.1/stdf/G4_MZMD15163_M88855.1_22_20230119.stdf"
    stdf_merge(fp1, fp2)
    # stdf_find_dup_testnum()