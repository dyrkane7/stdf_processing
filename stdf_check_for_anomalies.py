# -*- coding: utf-8 -*-
"""
Created on Sun Feb 19 21:12:37 2023

@author: dkane
"""
# -check invalid bin numbers
#   -if tester crashes, part gets HW/SW bin 65535, which is invalid bin number
# -check dup test number
# -check die part number

from Semi_ATE.STDF import utils

import os
from datetime import datetime
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog

# def write_stdf_validation_log(msg, )

def stdf_check_bin_numbers(stdf_fp = ""):
    if stdf_fp == "":  
        stdf_fp = filedialog.askopenfilename()
    
    stdf_fp = os.path.abspath(stdf_fp)
    stdf_filename = os.path.basename(stdf_fp)
    stdf_dir = os.path.dirname(stdf_fp)
    print("stdf file name:", stdf_filename)
    print("stdf directory:", stdf_dir)
    print("CHECKING FOR INVALID BIN NUM...")
    
    assert os.path.isfile(stdf_fp), "the file does not exist:\n{}".format(stdf_fp)
    assert utils.is_STDF(stdf_fp), "the file is not stdf file:\n{}".format(stdf_fp)
    endian, version = utils.endian_and_version_from_file(stdf_fp)

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
            pid = rec_obj.get_fields('PART_ID')[3]
            if sbin == 65535 or hbin == 65535:
                invalid_part_i.append(part_count)
                print("Found PRR with invalid bin#:", "x:", x, "y:", y,"hbin:", hbin, "sbin:", sbin, "part id:", pid, "prr count:", part_count)
        elif (rec_type,rec_sub) == id_ts_dict["SBR"]:
            rec_obj = utils.create_record_object(version, endian, "SBR", raw_bytes)
            if rec_obj.get_fields('SBIN_NUM')[3] == 65535:
                print("Found invalid SBR - bin# 65535")
        elif (rec_type,rec_sub) == id_ts_dict["HBR"]:
            rec_obj = utils.create_record_object(version, endian, "HBR", raw_bytes)
            if rec_obj.get_fields('HBIN_NUM')[3] == 65535:
                print("Found invalid HBR - bin# 65535")

def stdf_check_for_dup_testnum(stdf_fp = ""):
    if stdf_fp == "":  
        stdf_fp = filedialog.askopenfilename()
        
    # dt0 = datetime.now()
    # print("Start time: ", dt0)
    
    stdf_fp = os.path.abspath(stdf_fp)
    stdf_filename = os.path.basename(stdf_fp)
    stdf_dir = os.path.dirname(stdf_fp)
    print("stdf file name:", stdf_filename)
    print("stdf directory:", stdf_dir)
    print("CHECKING FOR DUP TESTNUM...")
    
    assert os.path.isfile(stdf_fp), "the file does not exist:\n{}".format(stdf_fp)
    assert utils.is_STDF(stdf_fp), "the file is not stdf file:\n{}".format(stdf_fp)
    endian, version = utils.endian_and_version_from_file(stdf_fp)

    ptr_dup_tnum_i = [] # indices of records with duplicate 
    ptr_dup_tnum_dict = {} # 
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
                    info = (tnam, tnum_tnam_dict[tnum], tnum)
                    if info not in ptr_dup_tnum_dict:
                        ptr_dup_tnum_dict[info] = 1
                    else:
                        ptr_dup_tnum_dict[info] += 1
                    # print("Found different test names with same test number:")
                    # print("test name 1:", tnam, ", test name 2:", tnum_tnam_dict[tnum], ", test num:", tnum)
            elif tnam in tnam_tnum_dict:
                assert tnum == tnam_tnum_dict[tnam], "found PTR's with same test name but different test number:\n{} {}\n{} {}".format(tnam, tnum, tnam, tnam_tnum_dict[tnam])
            else:
                tnum_tnam_dict[tnum] = tnam
                tnam_tnum_dict[tnam] = tnum
    for info in ptr_dup_tnum_dict:
        print(info, "count:", ptr_dup_tnum_dict[info])

if __name__ == '__main__':
    fp = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_11_20230110.stdf" # dup testnums
    fp_list = []
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_02_20230213.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_04_20230213.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_06_20230213.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/G4_MZMD15163_N12126.1_02_20230203.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/G4_MZMD15163_N12126.1_04_20230203.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/G4_MZMD15163_N12126.1_06_20230211.stdf")
    
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/G4_MZMD15163_N12126.1_10_20230217.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/G4_MZMD15163_N12126.1_12_20230217.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/partial wafer8/G4_MZMD15163_N12126.1_08_20230217.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/partial wafer8/G4_MZMD15163_N12126.1_08_20230211.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/partial wafer14/G4_MZMD15163_N12126.1_14_20230217.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/partial wafer14/G4_MZMD15163_N12126.1_14_20230221.stdf")

    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_08_20230213.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_10_20230213.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_12_20230213.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_14_20230213.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_16_20230215.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_17_20230215.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_18_20230215.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_20_20230215.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_21_20230215.stdf")
    # fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/G4_TIA25133_N12126.1_24_20230215.stdf")
    
    fp_list.append(r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/TIA/edited/G4_TIA25133_N12126.1_15_20230110.stdf")
    
    for fp in fp_list:
        stdf_check_bin_numbers(fp)
    for fp in fp_list:
        stdf_check_for_dup_testnum(fp)