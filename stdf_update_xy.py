# -*- coding: utf-8 -*-
"""
Created on Mon May 15 20:29:49 2023

@author: dkane
"""

import os

from tkinter import filedialog
from Semi_ATE.STDF import utils

def stdf_update_xy(update_xy, stdf_fp = ""):
    if stdf_fp == "":  
        stdf_fp = filedialog.askopenfilename()
        
    stdf_fp = os.path.abspath(stdf_fp)
    stdf_fn = os.path.basename(stdf_fp)
    stdf_dir = os.path.dirname(stdf_fp)
    print("stdf file name:", stdf_fn)
    print("stdf directory:", stdf_dir)
    
    assert os.path.isfile(stdf_fp), "the file does not exist:\n{}".format(stdf_fp)
    assert utils.is_STDF(stdf_fp), "the file is not stdf file:\n{}".format(stdf_fp)
    endian, version = utils.endian_and_version_from_file(stdf_fp)
    
    fp_wo_ext, ext = os.path.splitext(stdf_fp)
    new_stdf_fp = fp_wo_ext + "_rev1" + ext
    # print(new_stdf_fp)
    with open(new_stdf_fp, 'wb') as new_stdf:
        id_ts_dict = utils.id_to_ts()
        for rec in utils.check_records_from_file(stdf_fp):
            _, rec_type, rec_sub, raw_bytes = rec
            if (rec_type,rec_sub) == id_ts_dict["PRR"]:
                rec_obj = utils.create_record_object(version, endian, "PRR", raw_bytes)
                x = rec_obj.get_fields('X_COORD')[3]
                y = rec_obj.get_fields('Y_COORD')[3]
                x, y = update_xy(x, y)
                rec_obj.set_value('X_COORD', x)
                rec_obj.set_value('Y_COORD', y)
                raw_bytes = rec_obj.__repr__()
            new_stdf.write(raw_bytes)
    return new_stdf_fp
            

if __name__ == "__main__":
    fp_p1 = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Integra-Job/Cisco/BigBen/Stdf/5AIX5202-P102.std"
    fp_p2 = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Integra-Job/Cisco/BigBen/Stdf/5AIX5202-P202.std"
    fp_p3 = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Integra-Job/Cisco/BigBen/Stdf/5AIX5202-P202.std"
    
    # I3 and I4 dies
    def update_xy_p1(x,y):
        ret_x = x*5 + 4
        ret_y = y*8 + 2
        return ret_x, ret_y
    # I1 and J1 dies
    def update_xy_p2(x,y):
        if x % 2: # if odd
            ret_x = x*5 + 4
        else:     # if even
            ret_x = x*5
        ret_y = y*8 + 6
        return ret_x, ret_y
    # I2 and J2 dies
    def update_xy_p3(x,y):
        if x % 2: # if odd
            ret_x = x*5
        else:     # if even
            ret_x = x*5 + 4
        ret_y = y*8 + 6
        return ret_x, ret_y
    
    stdf_update_xy(update_xy_p1, fp_p1)
    stdf_update_xy(update_xy_p2, fp_p2)
    stdf_update_xy(update_xy_p3, fp_p3)
    
    # stdf_update_xy()
    
