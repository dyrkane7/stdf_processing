# -*- coding: utf-8 -*-
"""
Created on Sat Dec 31 19:11:21 2022

@author: dkane
"""

# This program assumes first pass all dies tested and 2nd pass fail dies tested
# Wafer map will use 

from Semi_ATE.STDF import utils
import xlsxwriter

import os
from datetime import datetime
from datetime import timedelta
# import tkinter as tk
from tkinter import filedialog
# from time import gmtime
# from wafer_map import wm_app

# root = tk.Tk()
# root.withdraw()


def get_max_xy(die_info):
    x_max, y_max = 0, 0
    for x, y in die_info:
        x_max = x if x > x_max else x_max
        y_max = y if y > y_max else y_max
    return x_max, y_max

def write_wafermap_border(die_info, ws):
    x_max, y_max = get_max_xy(die_info)
    row_max_x, col_max_y = [0] * y_max, [0] * x_max
    row_min_x, col_min_y = [9999] * y_max, [9999] * x_max
    for x, y in die_info:
        row_max_x[y-1] = x if x > row_max_x[y-1] else row_max_x[y-1]
        row_min_x[y-1] = x if x < row_min_x[y-1] else row_min_x[y-1]
        col_max_y[x-1] = y if y > col_max_y[x-1] else col_max_y[x-1]
        col_min_y[x-1] = y if y < col_min_y[x-1] else col_min_y[x-1]
    for x, y in die_info:
        if row_max_x[y-1] == x:
            die_info[(x,y)]["format"].set_right(1)
        if row_min_x[y-1] == x:
            die_info[(x,y)]["format"].set_left(1)
        if col_max_y[x-1] == y:
            die_info[(x,y)]["format"].set_bottom(1)
        if col_min_y[x-1] == y:
            die_info[(x,y)]["format"].set_top(1)

def stdf_wafer_map(stdf_fp = ""):
    
    colors = [
        '#ffffff', '#ffe119', '#4363d8', '#e6194b', 
        '#f58231', '#911eb4', '#46f0f0', '#f032e6', 
        '#bcf60c', '#fabebe', '#008080', '#e6beff', 
        '#9a6324', '#fffac8', '#aaffc3', 
        '#808000', '#ffd8b1', '#808080', 
    ]
    
    dt0 = datetime.now()
    print("Start time: ", dt0)
    
    if stdf_fp == "":  
        stdf_fp = filedialog.askopenfilename()

    stdf_fp = os.path.abspath(stdf_fp)
    stdf_filename = os.path.basename(stdf_fp)
    stdf_dir = os.path.dirname(stdf_fp)
    print("stdf file name:", stdf_filename)
    print("stdf directory:", stdf_dir)
    
    assert os.path.isfile(stdf_fp), "the file does not exist:\n{}".format(stdf_fp)
    assert utils.is_STDF(stdf_fp), "the file is not stdf file:\n{}".format(stdf_fp)
    endian, version = utils.endian_and_version_from_file(stdf_fp)
    
    stdf_fileroot = os.path.splitext(stdf_filename)[0]
    xlsx_fp = stdf_dir + '\\' + stdf_fileroot + '_map.xlsx'
    print("xlsx filename:", os.path.basename(xlsx_fp))
    
    wb = xlsxwriter.Workbook(xlsx_fp)
    ws = wb.add_worksheet("wafer map")
    ws.set_zoom(70)
    ws.freeze_panes(1,1)
    
    setup_time, start_time, stop_time, total_test_time = 0, 0, 0, 0
    print(setup_time, start_time, stop_time)
    die_info = {} # {(<x>,<y>) : (<soft_bin>, <xlsx_format>)}
    sbin_info = {}
    sbin_info[1] = {"name": "GOOD_BIN1", "count": 0}
    global_info = {"part count" : 0, "retest count" : 0, "good count" : 0,
                   "start time" : "", "setup time" : "", "stop time" : "", "elapsed time": "",
                   "total test time": ""} # total test time is sum of test time for each part (excludes index time, cleaning time, down time)
    id_ts_dict = utils.id_to_ts()
    for rec in utils.check_records_from_file(stdf_fp):
        _, rec_type, rec_sub, raw_bytes = rec
        if (rec_type,rec_sub) == id_ts_dict["MIR"]:
            rec_obj = utils.create_record_object(version, endian, "MIR", raw_bytes)
            setup_time = rec_obj.get_fields('SETUP_T')[3]
            start_time = rec_obj.get_fields('START_T')[3]
            global_info["lot id"] = rec_obj.get_fields('LOT_ID')[3]
            global_info["part type"] = rec_obj.get_fields('PART_TYP')[3]
            global_info["test program"] = rec_obj.get_fields('JOB_NAM')[3]
            global_info["sw version"] = rec_obj.get_fields('EXEC_VER')[3]
            print("MIR")
        if (rec_type,rec_sub) == id_ts_dict["MRR"]: # no MRR for incomplete stdf
            rec_obj = utils.create_record_object(version, endian, "MRR", raw_bytes)
            stop_time = rec_obj.get_fields('FINISH_T')[3]
            print("MRR")
        if (rec_type,rec_sub) == id_ts_dict["PCR"]: # no PCR for incomplete stdf
            rec_obj = utils.create_record_object(version, endian, "PCR", raw_bytes)
            # global_info["part count"] = rec_obj.get_fields('PART_CNT')[3]
            # global_info["retest count"] = rec_obj.get_fields('RTST_CNT')[3]
            # global_info["good count"] = rec_obj.get_fields('GOOD_CNT')[3]
            print("PCR")
        if (rec_type,rec_sub) == id_ts_dict["SBR"]: # no SBR for incomplete stdf
            rec_obj = utils.create_record_object(version, endian, "SBR", raw_bytes)
            sbin_name = rec_obj.get_fields('SBIN_NAM')[3]
            sbin_num = rec_obj.get_fields('SBIN_NUM')[3]
            # sbin_count = rec_obj.get_fields('SBIN_CNT')[3]
            sbin_info[sbin_num]["name"] = sbin_name
            sbin_info[sbin_num]["count"] = 0
            print("SBR")
        if (rec_type,rec_sub) == id_ts_dict['PRR']:
            rec_obj = utils.create_record_object(version, endian, "PRR", raw_bytes)
            x = rec_obj.get_fields('X_COORD')[3]
            y = rec_obj.get_fields('Y_COORD')[3]
            soft_bin = rec_obj.get_fields('SOFT_BIN')[3]
            test_t = rec_obj.get_fields('TEST_T')[3]
            total_test_time += test_t
            part_flag = rec_obj.get_fields('PART_FLG')[3]
            if (x,y) not in die_info: # if new part (not retest part)
                global_info["part count"] += 1
            else: # if retest part (not new part)
                global_info["retest count"] += 1
            # if not int(part_flag[-4]): # if new part passed (bit = 0)
            #     global_info["good count"] += 1
            if soft_bin not in sbin_info:
                sbin_info[soft_bin] = {"name": "", "count": 0}

            if (x,y) not in die_info or not int(part_flag[-4]): # if new part or part passed
                die_info[(x, y)] = {"soft bin" : soft_bin, "format" : wb.add_format()}

    
    for x,y in die_info:
        if die_info[(x,y)]["soft bin"] == 1:
            global_info["good count"] += 1
        soft_bin = die_info[(x,y)]["soft bin"]
        # if soft_bin not in sbin_info:
        #     sbin_info[soft_bin] = {"name":"", "count":0}
        sbin_info[soft_bin]["count"] += 1
    x_max, y_max = get_max_xy(die_info)
    print("x_max:", x_max, ", y_max:", y_max)
    print("# of dies:", global_info["part count"])

    cell_format = wb.add_format()
    cell_format.set_center_across()
    for x in range(x_max):
        ws.write(0, x+2, 'X{}'.format(x+1), cell_format)
    for y in range(y_max):
        ws.write(y+2, 0, 'Y{}'.format(y+1), cell_format)
    
    bin_colors = {} # {<soft_bin>: <color_str>}
    bin_colors[1] = "#3cb44b" # bin 1 always green
    write_wafermap_border(die_info, ws)
    for x, y in die_info:
        soft_bin = die_info[(x,y)]["soft bin"]
        cell_format = die_info[(x,y)]["format"]
        if soft_bin not in bin_colors:
            bin_colors[soft_bin] = colors.pop() if len(colors) > 1 else colors[0]
        cell_format.set_bg_color(bin_colors[soft_bin])
        cell_format.set_center_across()
        ws.write(y+1, x+1, soft_bin, cell_format)
    
    header = ["Bin Code", "Name", "%Yield", "Count"]
    for i, string in enumerate(header):
        ws.write(2, x_max + 4 + i, string)
    print("bin codes:", bin_colors.keys())
    if bin_colors.keys():
        for y, soft_bin in enumerate(sorted(bin_colors.keys())):
            cell_format = wb.add_format()
            cell_format.set_bg_color(bin_colors[soft_bin])
            cell_format.set_center_across()
            ws.write(y + 3, x_max + 4, soft_bin, cell_format)
            try:
                ws.write(y + 3, x_max + 5, sbin_info[soft_bin]["name"])
            except KeyError:
                print("key error ({}). This might be caued by missing SBR".format(soft_bin))
            percent_yield = 100 * sbin_info[soft_bin]["count"] / global_info["part count"]
            ws.write(y + 3, x_max + 6, "{:.2f}".format(percent_yield))
            ws.write(y + 3, x_max + 7, sbin_info[soft_bin]["count"])
    
    # add 8*3600 seconds to set PST timezone (8 hours ahead of UST)
    global_info["start time"] = datetime.fromtimestamp(start_time + 8*3600).strftime('%Y-%m-%d %H:%M:%S')
    t = stop_time - start_time
    global_info["setup time"] = datetime.fromtimestamp(setup_time + 8*3600).strftime('%Y-%m-%d %H:%M:%S')
    global_info["stop time"] = datetime.fromtimestamp(stop_time + 8*3600).strftime('%Y-%m-%d %H:%M:%S')
    global_info["elapsed time"] = "{:.2f} hours".format(t/3600)
    global_info["total test time"] = "{:.2f} hours".format(total_test_time/(3600*1000))
        
    print(global_info)
    for y, key in enumerate(global_info):
        ws.write(y + 2, x_max + 9, key)
        ws.write(y + 2, x_max + 10, global_info[key])
    
    wb.close()
    
    # open file in excel
    # add quotes around any directory name with spaces, or system command wont work
    splits = xlsx_fp.split('\\')
    tmp = ""
    for split in splits:
        if  ' ' in split:
            split = ('"' + split + '"')
        tmp += (split + "\\")
    xlsx_fp = tmp[0:-1]
    os.system(xlsx_fp)
    
    dt1 = datetime.now()
    delta = timedelta()
    delta = dt1 - dt0
    print("\nEnd time: ", dt1)
    print("Elapsed time: ", delta)

if __name__ == '__main__':
    # fp_list = [
    #     r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 6/M99545.1/stdf/G6_XCVR6775131_M99545.1_02_20230120.stdf_inc",
    #     ]
    
    fps= filedialog.askopenfilenames()
    for fp in fps:
        stdf_wafer_map(fp)