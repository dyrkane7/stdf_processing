# -*- coding: utf-8 -*-
"""
Created on Thu Oct 12 20:12:20 2023

@author: dkane

This module is initially created to merge STDF files 
from manual test of Portico wafers. 

TODO: Update to handle STDF files from other test programs 

!!! WARNING !!! This module is designed to merge STDF files from 93k manual wafer sort
"""


import struct
import sys
import os
import statistics
from datetime import datetime
from datetime import timedelta
from tkinter import filedialog

from Semi_ATE.STDF import utils
from Semi_ATE.STDF import (ATR, BPS, CDR, CNR, DTR, EPS, FAR, FTR, GDR, HBR, MIR, MPR, MRR, 
                NMR, PCR, PGR, PIR, PLR, PMR, PRR, PSR, PTR, RDR, SBR, SDR, SSR, 
                STR, TSR, VUR, WIR, WCR, WRR)

from stdf_file import STDFFile
from stdf_to_atdf import stdf_to_atdf

# TODO: update this method to handle arbitrary number of part sequences in both files
def stdf_merge_part_sequences(stdf1, stdf2):
    
    # Get STDF2 first part sequence records
    recs = []
    for offset in stdf2.index['parts'][1]: # first part key is 1
        recs.append(stdf2.index['indexes'][offset])
    
    # Insert STDF2 part sequence into STDF1
    offset = stdf1.index['records']['WRR'][0] # get index of first WRR
    stdf1.insert_records(recs, offset, is_new_part_seq=True)
    
    # Debug start
    # for part_id in stdf1.index['parts']:
    #     print("part_id:", part_id)
    #     print("part_id record count:", len(stdf1.index['parts'][part_id]))
    # Debug stop
    
    return stdf1

def stdf_merge_hbr(stdf1, stdf2):
    stdf2_rec_objects = stdf2.get_rec_objects({"HBR" : []})
    stdf1_rec_objects = stdf1.get_rec_objects({"HBR" : []})
    stdf1_bin_nums = [obj.get_value("HBIN_NUM") for obj in stdf1_rec_objects['HBR'].values()]
    stdf2_bin_nums = [obj.get_value("HBIN_NUM") for obj in stdf2_rec_objects['HBR'].values()]
    for bin_num, rec_obj in zip(stdf2_bin_nums, stdf2_rec_objects['HBR'].values()):
        if bin_num not in stdf1_bin_nums:
            offset = stdf1.index['records']['SBR'][0] # assumes at least 1 SBR in STDF #1
            stdf1.insert_record(rec_obj.__repr__(), "HBR", offset)
    return stdf1
            
def stdf_merge_sbr(stdf1, stdf2):
    stdf2_rec_objects = stdf2.get_rec_objects({"SBR" : []})
    stdf1_rec_objects = stdf1.get_rec_objects({"SBR" : []})
    stdf1_bin_nums = [obj.get_value("SBIN_NUM") for obj in stdf1_rec_objects['SBR'].values()]
    stdf2_bin_nums = [obj.get_value("SBIN_NUM") for obj in stdf2_rec_objects['SBR'].values()]
    for bin_num, rec_obj in zip(stdf2_bin_nums, stdf2_rec_objects['SBR'].values()):
        if bin_num not in stdf1_bin_nums:
            offset = stdf1.index['records']['PCR'][0] # assumes PCR exists in STDF #1
            stdf1.insert_record(rec_obj.__repr__(), "SBR", offset)
    return stdf1

#TODO implement this
# stdf1 finish time gets set to stdf2 finish time
def stdf_update_finish_t(stdf1, stdf2):
    print("test")
    
    return stdf1
    
# TODO: add method to merge TSR
def stdf_merge(stdf_objects):
    merged_stdf = stdf_objects[0]
    for stdf in stdf_objects[1:]:
        merged_stdf = stdf_merge_part_sequences(merged_stdf, stdf)
        merged_stdf = stdf_merge_sbr(merged_stdf, stdf)
        merged_stdf = stdf_merge_hbr(merged_stdf, stdf)
        # merged_stdf = stdf_update_finish_t(merged_stdf, stdf)
    merged_stdf.update_hbin_cnts()
    merged_stdf.update_sbin_cnts()
    merged_stdf.update_total_part_count()
    merged_stdf.update_pass_part_count()
    merged_stdf.update_retest_part_count()
    return merged_stdf

if __name__ == '__main__':
    fp1 = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Integra-Job/SEAKR/Portico/8DMX09001/Wafer 04 Pass 2 0C 10-11-2023 manual test/main_Lot_1_Oct_11_16h20m55s_STDF_X5Y4"
    fp2 = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Integra-Job/SEAKR/Portico/8DMX09001/Wafer 04 Pass 2 0C 10-11-2023 manual test/main_Lot_1_Oct_11_16h50m08s_STDF_X6Y4"
    
    fp1 = os.path.abspath(fp1)
    fp2 = os.path.abspath(fp2)
    
    stdf1 = STDFFile(fp1)
    stdf2 = STDFFile(fp2)
    
    dt0 = datetime.now()
    print("Start time: ", dt0)
    
    merged_stdf = stdf_merge([stdf1, stdf2])
    
    # new_fp = os.path.join(os.path.dirname(fp1), "test.stdf")
    
    # merged_stdf.write_stdf(new_fp, overwrite = True)
    
    dt1 = datetime.now()
    delta = timedelta()
    delta = dt1 - dt0
    print("\nEnd time: ", dt1)
    print("Elapsed time: ", delta)
    
    # stdf_to_atdf([new_fp], debug=False)
    