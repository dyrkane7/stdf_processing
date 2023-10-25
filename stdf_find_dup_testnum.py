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

def get_unused_tnum(test_dict):
    i = 0
    while 1:
        if i not in test_dict:
            return i
        i += 1
        
def stdf_find_dup_testnum(stdf_fp = ""):
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
    
    ptr_dup_tnum_i = [] # indices of records with duplicate 
    tnum_tnam_dict = {}
    tnam_tnum_dict = {}
    tsr_list = []
    part_count = 0
    id_ts_dict = utils.id_to_ts()
    for i, rec in enumerate(utils.check_records_from_file(stdf_fp)):
        _, rec_type, rec_sub, raw_bytes = rec
        if (rec_type,rec_sub) == id_ts_dict["TSR"]:
            rec_obj = utils.create_record_object(version, endian, "TSR", raw_bytes)
            tnam = rec_obj.get_fields('TEST_NAM')[3]
            tnum = rec_obj.get_fields('TEST_NUM')[3]
            tsr_list.append({"tnam" : tnam, "tnum" : tnum})
        elif (rec_type,rec_sub) == id_ts_dict["PRR"]:
            rec_obj = utils.create_record_object(version, endian, "PRR", raw_bytes)
            x = rec_obj.get_fields('X_COORD')[3]
            y = rec_obj.get_fields('Y_COORD')[3]
            part_count += 1
            if not part_count % 50:
                print("x:", x, "y:", y, "part count:", part_count)
        elif (rec_type,rec_sub) == id_ts_dict["PTR"]:
            rec_obj = utils.create_record_object(version, endian, "PTR", raw_bytes)
            tnam = rec_obj.get_fields('TEST_TXT')[3]
            tnum = rec_obj.get_fields('TEST_NUM')[3]
            if tnum in tnum_tnam_dict:
                if tnam != tnum_tnam_dict[tnum]: # if same test_num but different test_name
                    ptr_dup_tnum_i.append(i)
                    print("FOUND DUP TEST NUM")
                    # dup_test_list.append({"test_name":test_txt, "test_num":test_num})
                    # print("Found PTR with same test# but different test name:")
                    # print(test_num, test_txt, "\n", test_num, test_dict[test_num])
            elif tnam in tnam_tnum_dict:
                assert tnum == tnam_tnum_dict[tnam], "found PTR's with same test name but different test number:\n{} {}\n{} {}".format(tnam, tnum, tnam, tnam_tnum_dict[tnam])
                # if tnum != tnam_tnum_dict[tnam]:
                #     ptr_dup_tnam_i.append(i)
                #     print("FOUND DUP TEST NAME")
            else:
                # test_num_list.append(test_num)
                tnum_tnam_dict[tnum] = tnam
                tnam_tnum_dict[tnam] = tnum
                
    print("FIRST PASS COMPLETE")            
    for i, rec in enumerate(utils.check_records_from_file(stdf_fp)):
        _, rec_type, rec_sub, raw_bytes = rec
        if i in ptr_dup_tnum_i:
            assert (rec_type,rec_sub) == id_ts_dict["PTR"]
            rec_obj = utils.create_record_object(version, endian, "PTR", raw_bytes)
            tnam = rec_obj.get_fields('TEST_TXT')[3]
            if tnam in tnam_tnum_dict:
                new_tnum = tnam_tnum_dict[tnam]
            else:
                new_tnum = get_unused_tnum(tnum_tnam_dict)
                tnam_tnum_dict[tnam] = new_tnum
                tnum_tnam_dict[new_tnum] = tnam
            # dup_tnam_tnum_dict[tnam] = new_tnum
            rec_obj.set_value('TEST_NUM', new_tnum)
            raw_bytes = rec_obj.__repr__()
        new_stdf.write(raw_bytes)
    
    # Check if any TSR have same test number but different test name
    for tsr1 in tsr_list:
        tnum1 = tsr1["tnum"]
        tnam1 = tsr1["tnam"]
        for tsr2 in tsr_list:
            tnum2 = tsr2["tnum"]
            tnam2 = tsr2["tnam"]
            if tnum1 == tnum2:
                assert tnam1 == tnam2, "found TSR with same test# and different test name:\n{} {}\n{} {}".format(tnum1, tnam1, tnum2, tnam2)
        
    new_stdf.close()
    dt1 = datetime.now()
    delta = timedelta()
    delta = dt1 - dt0
    print("\nEnd time: ", dt1)
    print("Elapsed time: ", delta)

if __name__ == '__main__':
    # fp = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/stdf errors/G6_XCVR6775131_M99546.1_22_20220906.stdf"
    fp = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_15_20230110.stdf"
    stdf_find_dup_testnum(fp)
    # stdf_find_dup_testnum()