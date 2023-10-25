# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 19:03:37 2023

@author: dkane
"""
from Semi_ATE.STDF import utils

import os
from datetime import datetime
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog

def stdf_get_n_records(fp):
    n_records = 0
    for rec in utils.check_records_from_file(fp):
        n_records += 1
    return n_records

def stdf_compare_records(fp1, fp2):
    gen1 = utils.check_records_from_file(fp1)
    gen2 = utils.check_records_from_file(fp2)
    mismatch_bytes_dict = {} # keys are 2-tuples of (rec2 id, rec2 id), values are number of rec pairs with mismatch bytes
    n_rec_type_mismatch = 0
    n_rec_sub_mismatch = 0
    n_raw_bytes_mismatch = 0
    # id_ts_dict = utils.id_to_ts()
    ts_id_dict = utils.ts_to_id()
    endian1, version1 = utils.endian_and_version_from_file(fp1)
    endian2, version2 = utils.endian_and_version_from_file(fp2)
    for rec1, rec2 in zip(gen1, gen2):
        _, rec1_type, rec1_sub, rec1_raw_bytes = rec1
        _, rec2_type, rec2_sub, rec2_raw_bytes = rec2
        if rec1_type != rec2_type:
            n_rec_type_mismatch += 1
        if rec1_sub != rec2_sub:
            n_rec_sub_mismatch += 1
        if rec1_raw_bytes != rec2_raw_bytes:
            rec1_id = ts_id_dict[(rec1_type,rec1_sub)]
            rec2_id = ts_id_dict[(rec2_type,rec2_sub)]
            if (rec1_id, rec2_id) not in mismatch_bytes_dict:
                mismatch_bytes_dict[(rec1_id, rec2_id)] = 0
            mismatch_bytes_dict[(rec1_id, rec2_id)] += 1
            n_raw_bytes_mismatch += 1

            rec1_obj = utils.create_record_object(version1, endian1, rec1_id, rec1_raw_bytes)
            rec2_obj = utils.create_record_object(version2, endian2, rec2_id, rec2_raw_bytes)
            # print("rec1_obj:", rec1_obj)
            # print("rec2_obj:", rec2_obj)
            # print("rec1_raw_bytes:", rec1_raw_bytes)
            # print("rec2_raw_bytes:", rec2_raw_bytes, end="\n\n")

    print("n_rec_type_mismatch:", n_rec_type_mismatch)
    print("n_rec_sub_mismatch:", n_rec_sub_mismatch)
    print("n_raw_bytes_mismatch:", n_raw_bytes_mismatch)
    for key in mismatch_bytes_dict:
        print(key, mismatch_bytes_dict[key], "record pair(s) with mismatch bytes")
    

if __name__ == '__main__':
    fp1 = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/python_scripts/semi ate stdf processing/stdf file/test files/5AIY1401-P125_072023.std"
    fp2 = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/python_scripts/semi ate stdf processing/stdf file/test files/5AIY1401-P125_072023_EDITED.stdf"
    assert os.path.isfile(fp1), "the file does not exist:\n{}".format(fp1)
    assert utils.is_STDF(fp1), "the file is not stdf file:\n{}".format(fp1)
    assert os.path.isfile(fp2), "the file does not exist:\n{}".format(fp2)
    assert utils.is_STDF(fp2), "the file is not stdf file:\n{}".format(fp2)
    n_records_f1 = stdf_get_n_records(fp1)
    n_records_f2 = stdf_get_n_records(fp2)
    print("# of records in file 1:", n_records_f1)
    print("# of records in file 2:", n_records_f2)
    stdf_compare_records(fp1, fp2)
    
    
    
    
    
    