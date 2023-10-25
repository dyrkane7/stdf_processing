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

# v3 changes
from Semi_ATE.STDF import utils
from Semi_ATE.STDF import ATR

import struct
import sys
import os
import statistics
from datetime import datetime
from datetime import timedelta
from tkinter import filedialog

class stdf_file_info:
    def __init__(self):
        self.part_info = {}
        self.test_info = {}
        self.src_fps = []
        self.index = {}
   
    def build_rec_index(self, fp):
        assert os.path.isfile(fp), "the file does not exist:\n{}".format(fp)
        assert utils.is_STDF(fp), "the file is not stdf file:\n{}".format(fp)
        self.index[fp] = {"recs":[], "TSRs":[], "PCRs":[], "SBRs":[], "HBRs":[]}
        endian, version = utils.endian_and_version_from_file(fp)
        id_ts_dict = utils.id_to_ts()
        part_i = 1
        for i, rec in enumerate(utils.check_records_from_file(fp)):
            _, rec_type, rec_sub, raw_bytes = rec
            self.index[fp]["recs"].append(rec)
            if (rec_type,rec_sub) == id_ts_dict["PIR"]:
                PTRs, FTRs = [], []
                start_i = i
            if (rec_type,rec_sub) == id_ts_dict["PTR"]:
                PTRs.append(rec)
            if (rec_type,rec_sub) == id_ts_dict["FTR"]:
                FTRs.append(rec)
                # debug start
                # rec_obj = utils.create_record_object(version, endian, "FTR", raw_bytes)
                # print(rec_obj)
                # debug stop
            if (rec_type,rec_sub) == id_ts_dict["PRR"]:
                stop_i = i
                self.index[fp][part_i] = {
                    "PRS":self.index[fp]["recs"][start_i:stop_i+1], "PTRs":PTRs, "FTRs":FTRs}
                part_i += 1
            if (rec_type,rec_sub) == id_ts_dict["WRR"]:
                self.index[fp]["WRR"] = rec
            if (rec_type,rec_sub) == id_ts_dict["TSR"]:
                # debug start
                # rec_obj = utils.create_record_object(version, endian, "TSR", raw_bytes)
                # if rec_obj.get_fields('TEST_TYP')[3] == 'F':
                #     print(rec_obj.get_fields('OPT_FLAG')[3])
                # degbu stop
                self.index[fp]["TSRs"].append(rec)
            if (rec_type,rec_sub) == id_ts_dict["PCR"]:
                self.index[fp]["PCRs"].append(rec)
            if (rec_type,rec_sub) == id_ts_dict["SBR"]:
                self.index[fp]["SBRs"].append(rec)
            if (rec_type,rec_sub) == id_ts_dict["HBR"]:
                self.index[fp]["HBRs"].append(rec)
            if (rec_type,rec_sub) == id_ts_dict["MRR"]:
                self.index[fp]["MRR"] = rec
        
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
                # print(part_i)
                
   # FTR (15,20) @ V4
   #    REC_LEN = '118' [U*2] (Bytes of data following header)
   #    REC_TYP = '15' [U*1] (Record type)
   #    REC_SUB = '20' [U*1] (Record sub-type)
   #    TEST_NUM = '123500' [U*4] (Test number)
   #    HEAD_NUM = '1' [U*1] (Test head number)
   #    SITE_NUM = '1' [U*1] (Test site number)
   #    TEST_FLG = '['0', '0', '0', '0', '0', '0', '0', '0']' [B*1] (Test flags (fail, alarm, etc.))
   #    OPT_FLAG = '['1', '1', '1', '1', '0', '1', '1', '1']' [B*1] (Optional data flag)
   #    CYCL_CNT = '0' [U*4] (Cycle count of vector)
   #    REL_VADR = '0' [U*4] (Relative vector address)
   #    REPT_CNT = '1' [U*4] (Repeat count of vector)
   #    NUM_FAIL = '0' [U*4] (Number of pins with 1 or more failures)
   #    XFAIL_AD = '0' [I*4] (X logical device failure address)
   #    YFAIL_AD = '0' [I*4] (Y logical device failure address)
   #    VECT_OFF = '0' [I*2] (Offset from vector of interest)
   #    RTN_ICNT = '0' [U*2] (Count (j) of return data PMR indexes)
   #    PGM_ICNT = '0' [U*2] (Count (k) of programmed state indexes)
   #    RTN_INDX = '[]' [xU*2] (Array of j return data PMR indexes) -> RTN_ICNT
   #    RTN_STAT = '[]' [xN*1] (Array of j returned states) -> RTN_ICNT
   #    PGM_INDX = '[]' [xU*2] (Array of k programmed state indexes) -> PGM_ICNT
   #    PGM_STAT = '[]' [xN*1] (Array of k programmed states) -> PGM_ICNT
   #    FAIL_PIN = '[]' [D*n] (Failing pin bitfield)
   #    VECT_NAM = 'GEN4_MZMD_spi_wr_rd_0xAA_01' [C*n] (Vector module pattern name)
   #    TIME_SET = '2,1,1' [C*n] (Time set name)
   #    OP_CODE = '' [C*n] (Vector Op Code)
   #    TEST_TXT = 'TF_SPI_WRITE_READ_0xAA:Functional[1]' [C*n] (Descriptive text or label)
   #    ALARM_ID = '' [C*n] (Name of alarm)
   #    PROG_TXT = '' [C*n] (Additional programmed information)
   #    RSLT_TXT = '' [C*n] (Additional result information)
   #    PATG_NUM = '255' [U*1] (Pattern generator number)
   #    SPIN_MAP = '[]' [D*n] (Bit map of enabled comparators)
            
   # example TSR:
   # TSR (10,30) @ V4
   #    REC_LEN = '87' [U*2] (Bytes of data following header)
   #    REC_TYP = '10' [U*1] (Record type)
   #    REC_SUB = '30' [U*1] (Record sub-type)
   #    HEAD_NUM = '255' [U*1] (Test head number)
   #    SITE_NUM = '0' [U*1] (Test site number)
   #    TEST_TYP = 'P' [C*1] (Test type [P/F/space])
   #    TEST_NUM = '31004' [U*4] (Test number)
   #    EXEC_CNT = '329' [U*4] (Number of test executions) #
   #    FAIL_CNT = '0' [U*4] (Number of test failures) #
   #    ALRM_CNT = '4294967295' [U*4] (Number of alarmed tests)
   #    TEST_NAM = 'VgaBits:VGADNL8@VGADNL8[5]' [C*n] (Test name)
   #    SEQ_NAME = '' [C*n] (Sequencer (program segment/flow) name)
   #    TEST_LBL = 'GEN4_MZMD_dummy_01' [C*n] (Test label or text)
   #    OPT_FLAG = '['1', '1', '0', '0', '1', '0', '0', '0']' [B*1] (Optional data flag See note)
   #    TEST_TIM = '3.452648401260376' [R*4] (Average test execution time in seconds)
   #    TEST_MIN = '-0.11750277131795883' [R*4] (Lowest test result value)
   #    TEST_MAX = '0.10418523848056793' [R*4] (Highest test result value)
   #    TST_SUMS = '-7.658430576324463' [R*4] (Sum of test result values)
   #    TST_SQRS = '0.4415596127510071' [R*4] (Sum of squares of test result values)
    
    # Note: lolim and hilim only included in first occurence of each PTR
    def update_test_info(self):
        assert len(self.part_info) > 0, "part_info is empty. Call update_part_info_from_file() before update_test_info()"
        for fp in self.src_fps:
            assert len(self.index[fp]["recs"]) > 0, "Record index is empty. Call build_rec_index() before update_test_info()"
        for part in self.part_info.values():
            part_i = part['part_i']
            fp = part['fp']
            endian, version = utils.endian_and_version_from_file(fp)
            ts_id_dict = utils.ts_to_id()
            for rec in (self.index[fp][part_i]["PTRs"] + self.index[fp][part_i]["FTRs"]):
                _, rec_type, rec_sub, raw_bytes = rec
                rec_id = ts_id_dict[(rec_type,rec_sub)]
                test_type = 'P' if rec_id == 'PTR' else 'F'
                rec_obj = utils.create_record_object(version, endian, rec_id, raw_bytes)
                tnam = rec_obj.get_fields('TEST_TXT')[3]
                tnum = rec_obj.get_fields('TEST_NUM')[3]
                if test_type == 'P':
                    result = rec_obj.get_fields('RESULT')[3]
                test_flg = rec_obj.get_fields('TEST_FLG')[3]
                is_fail = int(test_flg[0])
                is_alarm = int(test_flg[7])
                if tnum not in self.test_info:
                    self.test_info[tnum] = {
                        'tnam':tnam, 'tnum':tnum, 'exec_cnt':0, 
                        'fail_cnt':0, 'alarm_cnt':0, 'test_type':test_type, 'fp':fp}
                    if test_type == 'P':
                        self.test_info[tnum]['results'] = []
                if test_type == 'P':
                    self.test_info[tnum]['results'].append(result)
                self.test_info[tnum]['exec_cnt'] += 1
                if is_alarm:
                    self.test_info[tnum]['alarm_cnt'] += 1
                if is_fail:
                    self.test_info[tnum]['fail_cnt'] += 1
        for test in self.test_info.values():
            if test['test_type'] == 'P':
                test['test_min'] = min(test['results'])
                test['test_max'] = max(test['results'])
                test['test_sums'] = sum(test['results'])
                test_mean = statistics.mean(test['results'])
                test['test_sqrs'] = sum([(x - test_mean)**2 for x in test['results']])
        #debug start
        # for test in self.test_info['P'].values():
        #     print(test)
        # for test in self.test_info['F'].values():
        #     print(test)
        #debug stop
            
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
        assert len(self.part_info) > 0, "part_info dict is empty, Call update_part_info_from_file() to initialize part_info"
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
        assert len(self.part_info) > 0, "part_info dict is empty, Call update_part_info_from_file to initialize part info"
        sw_bin_cnts = {}
        for part_dict in self.part_info.values():
            if part_dict['sw_bin'] not in sw_bin_cnts:
                sw_bin_cnts[part_dict['sw_bin']] = 1
            else:
                sw_bin_cnts[part_dict['sw_bin']] += 1
        return sw_bin_cnts
    
    def get_hw_bin_cnts(self):
        assert len(self.part_info) > 0, "part_info dict is empty, Call update_part_info_from_file to initialize part info"
        hw_bin_cnts = {}
        for part_dict in self.part_info.values():
            if part_dict['hw_bin'] not in hw_bin_cnts:
                hw_bin_cnts[part_dict['hw_bin']] = 1
            else:
                hw_bin_cnts[part_dict['hw_bin']] += 1
        return hw_bin_cnts
                
    def get_part_cnt(self):
        assert len(self.part_info) > 0, "part_info dict is empty, Call update_part_info_from_file to initialize part info"
        part_cnt = len(self.part_info)
        return part_cnt
    
    def get_good_cnt(self):
        good_cnt = 0
        assert len(self.part_info) > 0, "part_info dict is empty, Call update_part_info_from_file to initialize part info"
        for part_dict in self.part_info.values():
            if part_dict['sw_bin'] == 1:
                good_cnt += 1
        return good_cnt
    
    def get_tsr_tnum_from_raw_bytes(self, raw_bytes):
        tnum = struct.unpack('I', raw_bytes[7:11])[0]
        return tnum



def write_merged_stdf_file(info): # takes as argument 'stdf_file_info' class
    assert len(info.src_fps), "Need at least 1 source file"
    fp1 = info.src_fps[0]
    file_dir = os.path.dirname(fp1)
    basename_wo_ext = os.path.splitext(os.path.basename(fp1))[0]
    splits = [x for x in basename_wo_ext.split('_') if not is_datecode(x)]
    fn_wo_datecode = "_".join(splits)
    fn = datetime.now().strftime(f"{fn_wo_datecode}_%Y%m%d")
    new_fp = file_dir + "/" + fn + "_MERGED.stdf"
    # assert not os.path.isfile(new_fp), "file already exists: {}".format(new_fp)
    if os.path.isfile(new_fp):
        inpt = input("\nFILE ALREADY EXISTS: {}\nOVERWRITE FILE (y/n)? 'n' will exit program:".format(os.path.basename(new_fp)))
        if inpt[0] == "n":
            sys.exit()
    print("new_fp:", new_fp)
    with open(new_fp, 'wb') as new_stdf:
        endian, version = utils.endian_and_version_from_file(fp1)
        id_ts_dict = utils.id_to_ts()
        ts_id_dict = utils.ts_to_id()
        
        # write recs up until first part result sequence
        insert_atr_flag = False
        for rec in utils.check_records_from_file(fp1):
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
            for i, rec in enumerate(info.index[fp][part_i]["PRS"]):
                _, rec_type, rec_sub, raw_bytes = rec
                if (rec_type,rec_sub) == id_ts_dict["PRR"]:
                    rec_obj = utils.create_record_object(version, endian, "PRR", raw_bytes)
                    part_flag = rec_obj.get_fields('PART_FLG')[3]
                    part_flag[-2] = "0" # new part (not retest)
                    rec_obj.set_value("PART_FLG", part_flag)
                    rec_obj.set_value("PART_ID", str(pid))
                    raw_bytes = rec_obj.__repr__()
                new_stdf.write(raw_bytes)
                
        # write single WRR
        _, rec_type, rec_sub, raw_bytes = info.index[fp1]['WRR']
        assert (rec_type,rec_sub) == id_ts_dict["WRR"], "Expected WRR"
        rec_obj = utils.create_record_object(version, endian, "WRR", raw_bytes)
        rec_obj.set_value("PART_CNT", info.get_part_cnt())
        rec_obj.set_value("GOOD_CNT", info.get_good_cnt())
        rec_obj.set_value("RTST_CNT", 0)
        raw_bytes = rec_obj.__repr__()
        new_stdf.write(raw_bytes)
        
        # write multiple TSR
        # recs = []
        # for fp in info.src_fps:
        #     recs += info.index[fp]["PTRs"]
        #     recs += info.index[fp]["FTRs"]
        # for rec in recs:
        #     _, rec_type, rec_sub, raw_bytes = rec
        #     rec_obj = utils.create_record_object(version, endian, ts_id_dict[(rec_type,rec_sub)], raw_bytes)
        #     tnum = rec_obj.get_fields("TEST_NUM")[3]
        #     tests = [x for x in info.test_info.values() if x['tnum'] == tnum]
        #     assert len(tests) == 1, f"expected 1 test with test# {tnum}. found {len(tests)}"
        #     test = tests[0]
        #     for rec in info.index[fp]["TSRs"]:
        
        n_tests = len(info.test_info.values())
        for test in info.test_info.values():
            fp = test['fp']
            found_match = False
            print("searching for test#", test["tnum"], "in TSR list...")
            for _, rec_type, rec_sub, raw_bytes in info.index[fp]["TSRs"]:
                if info.get_tsr_tnum_from_raw_bytes(raw_bytes) == test['tnum']:
                    found_match = True
                    print("found test#", test['tnum'], "in TSR list")
                    endian, version = utils.endian_and_version_from_file(fp)
                    rec_obj = utils.create_record_object(version, endian, "TSR", raw_bytes)
                    opt_flag = rec_obj.get_fields("OPT_FLAG")[3]
                    if rec_obj.get_fields("EXEC_CNT")[3] != 4294967295: # 4294967295 indicates missing/invalid data
                        rec_obj.set_value("EXEC_CNT", test["exec_cnt"])
                    else:
                        print("EXEC_CNT field contains missing or invalid data")
                    if rec_obj.get_fields("FAIL_CNT")[3] != 4294967295: # 4294967295 indicates missing/invalid data
                        rec_obj.set_value("FAIL_CNT", test["fail_cnt"])
                    else:
                        print("FAIL_CNT field contains missing or invalid data")
                    if rec_obj.get_fields("ALRM_CNT")[3] != 4294967295: # 4294967295 indicates missing/invalid data
                        rec_obj.set_value("ALRM_CNT", test["alarm_cnt"])
                    # else:
                        # print("ALARM_CNT field contains missing or invalid data")
                    # check OPT_FLAG fields
                    if opt_flag[7] == '0':
                        rec_obj.set_value("TEST_MIN", test["test_min"]) # bit 0
                    # else:
                    #     print("TEST_MIN field contains missing or invalid data")
                    if opt_flag[6] == '0':
                        rec_obj.set_value("TEST_MAX", test["test_max"]) # bit 1
                    # else:
                    #     print("TEST_MAX field contains missing or invalid data")
                    if opt_flag[3] == '0':
                        rec_obj.set_value("TST_SUMS", test["test_sums"]) # bit 4
                    # else:
                    #     print("TST_SUMS field contains missing or invalid data")
                    if opt_flag[2] == '0':
                        rec_obj.set_value("TST_SQRS", test["test_sqrs"]) # bit 5
                    # else:
                    #     print("TST_SQRS field contains missing or invalid data")
                    # write 2 TSR for each test
                    rec_obj.set_value("HEAD_NUM", 1)
                    rec_obj.set_value("SITE_NUM", 1)
                    raw_bytes = rec_obj.__repr__()
                    new_stdf.write(raw_bytes)
                    rec_obj.set_value("HEAD_NUM", 255)
                    rec_obj.set_value("SITE_NUM", 0)
                    raw_bytes = rec_obj.__repr__()
                    new_stdf.write(raw_bytes)
                    break
            n_tests -= 1
            print("tests remaining:", n_tests)
            assert found_match, f"found no match for test# {test['tnum']} in TSR list from file: {fp}"
        
        
        # write recs for: multiple HBR
        recs = []
        for fp in info.src_fps:
            recs += info.index[fp]["HBRs"]
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
            recs += info.index[fp]["SBRs"]
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
        
        # write 2 PCR
        for rec in info.index[fp1]["PCRs"]:
            _, rec_type, rec_sub, raw_bytes = rec
            rec_obj = utils.create_record_object(version, endian, "PCR", raw_bytes)
            rec_obj.set_value("PART_CNT", info.get_part_cnt())
            rec_obj.set_value("GOOD_CNT", info.get_good_cnt())
            rec_obj.set_value("RTST_CNT", 0)
            raw_bytes = rec_obj.__repr__()
            new_stdf.write(raw_bytes)
            
        # write MRR
        _, rec_type, rec_sub, raw_bytes = info.index[fp1]["MRR"]
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
    print("updating test_info...")
    info.update_test_info()
    info.reassign_pids()
    
    good_cnt = info.get_good_cnt()
    part_cnt = info.get_part_cnt()
    print("good_count:", good_cnt, "part_cnt:", part_cnt)
    sw_bin_cnts = info.get_sw_bin_cnts()
    hw_bin_cnts = info.get_hw_bin_cnts()
    print("sw_bin_cnts:", sw_bin_cnts, "\nhw_bin_cnts:", hw_bin_cnts)

    print("writing merged stdf file...")
    write_merged_stdf_file(info)

if __name__ == '__main__':
    fp_list = []
    fp1 = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/partial wafer14/G4_MZMD15163_N12126.1_14_20230217.stdf"
    fp2 = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Infinera/Gen 4/N12126.1/stdf/MZMD/partial wafer14/G4_MZMD15163_N12126.1_14_20230221.stdf"
    fp_list.append(fp1)
    fp_list.append(fp2)
    
    dt0 = datetime.now()
    print("Start time: ", dt0)
    
    stdf_merge(fp_list)
    
    dt1 = datetime.now()
    delta = timedelta()
    delta = dt1 - dt0
    print("\nEnd time: ", dt1)
    print("Elapsed time: ", delta)