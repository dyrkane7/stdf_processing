# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 19:38:30 2023

@author: dkane
"""

# This script merges 2 or more stdf files
# Merged file includes exactly 1 part result sequence per (x,y) coordinate
# If bin 1 result exists for (x,y), merged file will use the bin 1 part result sequence
# If no bin 1 result exists for (x,y), merged file will use the last occurence of (x,y) part result sequence
# SBR and HBR are updated to reflect final bin counts
# TSR records are not updated

from Semi_ATE.STDF import utils
from Semi_ATE.STDF import ATR

import os
from datetime import datetime
from tkinter import filedialog

class stdf_file_info:
    def __init__(self):
        self.part_info = {}
        self.src_fps = []
        self.index = {}
   
    def build_rec_index(self, fp):
        assert os.path.isfile(fp), "the file does not exist:\n{}".format(fp)
        assert utils.is_STDF(fp), "the file is not stdf file:\n{}".format(fp)
        self.index[fp] = {"recs":[], "tsr":[], "pcr":[], "sbr":[], "hbr":[]}
        endian, version = utils.endian_and_version_from_file(fp)
        id_ts_dict = utils.id_to_ts()
        part_i = 1
        for i, rec in enumerate(utils.check_records_from_file(fp)):
            _, rec_type, rec_sub, raw_bytes = rec
            self.index[fp]["recs"].append(rec)
            if (rec_type,rec_sub) == id_ts_dict["PIR"]:
                start_i = i
            if (rec_type,rec_sub) == id_ts_dict["PRR"]:
                stop_i = i
                self.index[fp][part_i] = {"start":start_i, "stop":stop_i}
                part_i += 1
            if (rec_type,rec_sub) == id_ts_dict["WRR"]:
                self.index[fp]["wrr"] = i
            if (rec_type,rec_sub) == id_ts_dict["TSR"]:
                self.index[fp]["tsr"].append(i)
            if (rec_type,rec_sub) == id_ts_dict["PCR"]:
                self.index[fp]["pcr"].append(i)
            if (rec_type,rec_sub) == id_ts_dict["SBR"]:
                self.index[fp]["sbr"].append(i)
            if (rec_type,rec_sub) == id_ts_dict["HBR"]:
                self.index[fp]["hbr"].append(i)
            if (rec_type,rec_sub) == id_ts_dict["MRR"]:
                self.index[fp]["mrr"] = i
        
    def update_part_info_from_file(self, fp):
        assert os.path.isfile(fp), "the file does not exist:\n{}".format(fp)
        assert utils.is_STDF(fp), "the file is not stdf file:\n{}".format(fp)
        if fp not in self.src_fps:
            self.src_fps.append(fp)
        endian, version = utils.endian_and_version_from_file(fp)
        id_ts_dict = utils.id_to_ts()
        part_i = 1
        for i, rec in enumerate(utils.check_records_from_file(fp)):
            _, rec_type, rec_sub, raw_bytes = rec
            if (rec_type,rec_sub) == id_ts_dict["PRR"]:
                rec_obj = utils.create_record_object(version, endian, "PRR", raw_bytes)
                pid = rec_obj.get_fields("PART_ID")[3]
                x = rec_obj.get_fields('X_COORD')[3]
                y = rec_obj.get_fields('Y_COORD')[3]
                hw_bin = rec_obj.get_fields('HARD_BIN')[3]
                sw_bin = rec_obj.get_fields('SOFT_BIN')[3]
                if (x,y) not in self.part_info:
                    self.part_info[(x,y)] = {'hw_bin':hw_bin, 'sw_bin':sw_bin, 'pid':pid, 'fp':fp, 'part_i':part_i}
                elif (x,y) in self.part_info and self.part_info[(x,y)]['sw_bin'] != 1:
                    self.part_info[(x,y)] = {'hw_bin':hw_bin, 'sw_bin':sw_bin, 'pid':pid, 'fp':fp, 'part_i':part_i}
                part_i += 1
        
    
        
    #     Y1  Y2  Y3  Y4  Y5  Y6
    # X1         (01)(02)          -->
    # X2     (06)(05)(04)(03)      <--
    # X3 (07)(08)(09)(10)(11)(12)  -->
    # X4 (18)(17)(16)(15)(14)(13)  <--
    # X5     (19)(20)(21)(22)      --> 
    # X6         (24)(23)          <--
    # PID sequence typically follows the above pattern
    # Use this function to reassign PIDs to conform to typical PID sequence (Serpentine prober stepping pattern)
    def reassign_pids(self):
        assert len(self.part_info) > 0, "part_info dict is empty, Call \"update_part_info_from_file()\" to initialize part_info"
        xy_list = list(self.part_info.keys())
        x_max = max([xy[0] for xy in xy_list])
        def xy_sort(xy):
            v1 = xy[1]
            v2 = xy[0] if xy[1] % 2 else x_max - xy[0]
            return (v1, v2)
        xy_list.sort(key = xy_sort)
        assert len(xy_list) == len(set(xy_list)),"found duplicates in xy_list {}".format([xy for xy in xy_list if xy_list.count(xy)>1])
        for (x,y) in self.part_info:
            self.part_info[(x,y)]['pid'] = str(xy_list.index((x,y)) + 1)
        
    def get_sw_bin_cnts(self):
        assert len(self.part_info) > 0, "part_info dict is empty, Call \"update_part_info_from_file\" to initialize part info"
        sw_bin_cnts = {}
        for part_dict in self.part_info.values():
            if part_dict['sw_bin'] not in sw_bin_cnts:
                sw_bin_cnts[part_dict['sw_bin']] = 1
            else:
                sw_bin_cnts[part_dict['sw_bin']] += 1
        return sw_bin_cnts
    
    def get_hw_bin_cnts(self):
        assert len(self.part_info) > 0, "part_info dict is empty, Call \"update_part_info_from_file\" to initialize part info"
        hw_bin_cnts = {}
        for part_dict in self.part_info.values():
            if part_dict['hw_bin'] not in hw_bin_cnts:
                hw_bin_cnts[part_dict['hw_bin']] = 1
            else:
                hw_bin_cnts[part_dict['hw_bin']] += 1
        return hw_bin_cnts
                
    def get_part_cnt(self):
        assert len(self.part_info) > 0, "part_info dict is empty, Call \"update_part_info_from_file\" to initialize part info"
        part_cnt = len(self.part_info)
        return part_cnt
    
    def get_good_cnt(self):
        good_cnt = 0
        assert len(self.part_info) > 0, "part_info dict is empty, Call \"update_part_info_from_file\" to initialize part info"
        for part_dict in self.part_info.values():
            if part_dict['sw_bin'] == 1:
                good_cnt += 1
        return good_cnt
    
def write_merged_stdf_file(info): # takes as argument 'stdf_file_info' class
    assert len(info.src_fps), "Need at least 1 source file"
    file_dir = os.path.dirname(info.src_fps[0])
    basename_wo_ext = os.path.splitext(os.path.basename(info.src_fps[0]))[0]
    splits = [x for x in basename_wo_ext.split('_') if not is_datecode(x)]
    fn_wo_datecode = "_".join(splits)
    fn = datetime.now().strftime(f"{fn_wo_datecode}_%Y%m%d")
    new_fp = file_dir + "/" + fn + "_MERGED.stdf"
    assert not os.path.isfile(new_fp), "file already exists: {}".format(new_fp)
    print("new_fp:", new_fp)
    with open(new_fp, 'wb') as new_stdf:
        endian, version = utils.endian_and_version_from_file(info.src_fps[0])
        id_ts_dict = utils.id_to_ts()
        ts_id_dict = utils.ts_to_id()
        
        # write recs up until first part result sequence
        insert_atr_flag = False
        for rec in utils.check_records_from_file(info.src_fps[0]):
            _, rec_type, rec_sub, raw_bytes = rec
            if (rec_type, rec_sub) == id_ts_dict["FAR"]:
                insert_atr_flag = True
            if (rec_type, rec_sub) == id_ts_dict["PIR"]:
                break
            new_stdf.write(raw_bytes)
            if insert_atr_flag:
                rec_obj = ATR(version=version, endian=endian)
                dt = datetime.now()
                program_info = "This is a merged file; Program name: " + os.path.basename(__file__) 
                for i, fp in enumerate(info.src_fps):
                    program_info += ("; file#{}: ".format(i+1) + os.path.basename(fp)) # add merged files
                rec_obj.set_value("MOD_TIM", int(dt.timestamp()))
                rec_obj.set_value("CMD_LINE", program_info)
                raw_bytes = rec_obj.__repr__()
                # print("rec length:", rec_obj.get_value("REC_LEN"))
                new_stdf.write(raw_bytes)
                insert_atr_flag = False
            
        # write part result sequences
        # repeated sequence of: single PIR > single GDR > mulitple PTR/FTR > single PRR
        for pid in range(1, len(info.part_info)+1):
            found_match = False
            for (x,y) in info.part_info:
                if info.part_info[(x,y)]["pid"] == str(pid):
                    assert not found_match, "found duplicate pid in part_info dict"
                    found_match = True
                    part_i = info.part_info[(x,y)]["part_i"]
                    fp = info.part_info[(x,y)]["fp"]
            assert found_match, "could not find match for pid {} in part_info".format(pid)
            start_i, stop_i = info.index[fp][part_i]["start"], info.index[fp][part_i]["stop"]
            for i, rec in enumerate(info.index[fp]["recs"][start_i:stop_i+1]):
                _, rec_type, rec_sub, raw_bytes = rec
                if (rec_type,rec_sub) == id_ts_dict["PRR"]:
                    rec_obj = utils.create_record_object(version, endian, "PRR", raw_bytes)
                    part_flag = rec_obj.get_fields('PART_FLG')[3]
                    part_flag[-2] = "0" # new part (not retest)
                    rec_obj.set_value("PART_FLG", part_flag)
                    rec_obj.set_value("PART_ID", str(pid))
                    raw_bytes = rec_obj.__repr__()
                new_stdf.write(raw_bytes)
                
        # write recs for: single WRR > multiple TSR
        start_i = info.index[info.src_fps[0]]["wrr"] 
        stop_i = max(info.index[info.src_fps[0]]["tsr"])
        for i, rec in enumerate(info.index[info.src_fps[0]]["recs"][start_i:stop_i+1]):
            _, rec_type, rec_sub, raw_bytes = rec
            if (rec_type,rec_sub) == id_ts_dict["WRR"]:
                rec_obj = utils.create_record_object(version, endian, "WRR", raw_bytes)
                rec_obj.set_value("PART_CNT", info.get_part_cnt())
                rec_obj.set_value("GOOD_CNT", info.get_good_cnt())
                rec_obj.set_value("RTST_CNT", 0)
                raw_bytes = rec_obj.__repr__()
            new_stdf.write(raw_bytes)
        
        #write recs for: multiple HBR
        recs = []
        for fp in info.src_fps:
            start_i = min(info.index[fp]["hbr"])
            stop_i = max(info.index[fp]["hbr"])
            recs += info.index[fp]["recs"][start_i:stop_i+1]
        hw_bin_cnts = info.get_hw_bin_cnts()
        for hbin in hw_bin_cnts:
            assert len(hw_bin_cnts), "expected 1 or more SW bins"
            for rec in recs:
                _, rec_type, rec_sub, raw_bytes = rec
                assert (rec_type,rec_sub) == id_ts_dict["HBR"], "expected HBR record. found {} record".format(ts_id_dict[(rec_type,rec_sub)])
                rec_obj = utils.create_record_object(version, endian, "HBR", raw_bytes)
                if rec_obj.get_fields('HBIN_NUM')[3] == hbin:
                    rec_obj.set_value('HBIN_CNT', hw_bin_cnts[hbin])
                    rec_obj.set_value('HEAD_NUM', 1)
                    rec_obj.set_value('SITE_NUM', 1)
                    raw_bytes = rec_obj.__repr__()
                    new_stdf.write(raw_bytes)
                    rec_obj.set_value('HEAD_NUM', 255)
                    rec_obj.set_value('SITE_NUM', 0)
                    raw_bytes = rec_obj.__repr__()
                    new_stdf.write(raw_bytes)
                    break
                    
        # write recs for: multiple SBR
        recs = []
        for fp in info.src_fps:
            start_i = min(info.index[fp]["sbr"])
            stop_i = max(info.index[fp]["sbr"])
            recs += info.index[fp]["recs"][start_i:stop_i+1]
        sw_bin_cnts = info.get_sw_bin_cnts()
        for sbin in sw_bin_cnts:
            assert len(sw_bin_cnts), "expected 1 or more SW bins"
            for rec in recs:
                _, rec_type, rec_sub, raw_bytes = rec
                assert (rec_type,rec_sub) == id_ts_dict["SBR"], "expected SBR record. found {} record".format(ts_id_dict[(rec_type,rec_sub)])
                rec_obj = utils.create_record_object(version, endian, "SBR", raw_bytes)
                if rec_obj.get_fields('SBIN_NUM')[3] == sbin:
                    rec_obj.set_value('SBIN_CNT', sw_bin_cnts[sbin])
                    rec_obj.set_value('HEAD_NUM', 1)
                    rec_obj.set_value('SITE_NUM', 1)
                    raw_bytes = rec_obj.__repr__()
                    new_stdf.write(raw_bytes)
                    rec_obj.set_value('HEAD_NUM', 255)
                    rec_obj.set_value('SITE_NUM', 0)
                    raw_bytes = rec_obj.__repr__()
                    new_stdf.write(raw_bytes)
                    break
        
        # write recs for: 2 PCR > single MRR
        start_i = min(info.index[info.src_fps[0]]["pcr"])
        stop_i = info.index[info.src_fps[0]]["mrr"]
        for i, rec in enumerate(info.index[info.src_fps[0]]["recs"][start_i:stop_i+1]):
            _, rec_type, rec_sub, raw_bytes = rec
            if (rec_type,rec_sub) == id_ts_dict["PCR"]:
                rec_obj = utils.create_record_object(version, endian, "PCR", raw_bytes)
                rec_obj.set_value("PART_CNT", info.get_part_cnt())
                rec_obj.set_value("GOOD_CNT", info.get_good_cnt())
                rec_obj.set_value("RTST_CNT", 0)
                raw_bytes = rec_obj.__repr__()
            new_stdf.write(raw_bytes)


def is_datecode(string):
    if string.isnumeric() and len(string) == 8:
        if int(string[0:4]) > 2000: # if year value is greater than 2000
            if int(string[4:6]) in range(1,13): # if month value is between 1 and 12 inclusive
                if int(string[6:8]) in range(1,32): # if day of month is between 1 and 31 inclusive
                    return True
    return False           
                
def stdf_merge(fp_list = []):
    if not fp_list:
        fp_list = filedialog.askopenfilenames()
    fn_list_wo_datecode = []
    for i, fp in enumerate(fp_list):
        fp = os.path.abspath(fp)
        print("fp{}: {}".format(i+1, fp))
        basename = os.path.basename(fp)
        basename_wo_ext = os.path.splitext(basename)[0]
        splits = [x for x in basename_wo_ext.split('_') if not is_datecode(x)]
        fn_list_wo_datecode.append("_".join(splits))
        print(fn_list_wo_datecode[i])
        assert fn_list_wo_datecode[0] == fn_list_wo_datecode[i], \
            "Merged STDF files must have the same die type, lot# and wafer#:\n{}\n{}".format(fn_list_wo_datecode[0], fn_list_wo_datecode[i])
        
    info = stdf_file_info()
    for fp in fp_list:
        info.update_part_info_from_file(fp)
        print("building rec index...")
        info.build_rec_index(fp)
    info.reassign_pids()
    
    good_cnt = info.get_good_cnt()
    part_cnt = info.get_part_cnt()
    print("good_count:", good_cnt, "part_cnt:", part_cnt)
    sw_bin_cnts = info.get_sw_bin_cnts()
    hw_bin_cnts = info.get_hw_bin_cnts()
    print("sw_bin_cnts:", sw_bin_cnts, "\nhw_bin_cnts:", hw_bin_cnts)

    write_merged_stdf_file(info)

if __name__ == '__main__':
    fp_list = []
    # fp1 = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/partial wafer14/G4_MZMD15163_N12126.1_14_20230217.stdf"
    # fp2 = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/partial wafer14/G4_MZMD15163_N12126.1_14_20230221.stdf"
    # fp_list.append(fp1)
    # fp_list.append(fp2)
    
    stdf_merge(fp_list)