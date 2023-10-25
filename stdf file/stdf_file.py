# -*- coding: utf-8 -*-
"""
Created on Wed May 24 22:41:44 2023

@author: dkane
"""

import os
import pandas as pd
import struct
import statistics
from datetime import datetime
from datetime import timedelta 
import bisect

from tqdm import tqdm
from tkinter import filedialog
from Semi_ATE.STDF import utils
from Semi_ATE.STDF import (ATR, BPS, CDR, CNR, DTR, EPS, FAR, FTR, GDR, HBR, MIR, MPR, MRR, 
                NMR, PCR, PGR, PIR, PLR, PMR, PRR, PSR, PTR, RDR, SBR, SDR, SSR, 
                STR, TSR, VUR, WIR, WCR, WRR)


'''
STDF files generated by Wafer Sort programs *are* supported

STDF files generated by Final Test programs *are not* supported
    -part counts and bin counts based on (x,y)

Write STDF flow:
    1) read records from file into index dict
    2) make changes to index dict
    3) write records to stdf file
'''
class STDFFile:
    MAX_4BYTE_FLOAT = 3.402823466e38
    MIN_4BYTE_FLOAT = -3.40282347e+38
    '''
        initialize 
    '''
    def __init__(self, fp, progress = False):
        self.fp = fp
        self.progress = progress
        self.index = self._index_stdf(self.fp)
        self.test_num_name_dict = self._get_test_num_nam_dict()
        
    def _index_stdf(self, fp):
        index = {}
        offset = 0
        
        if utils.is_STDF(fp):
            endian, version = utils.endian_and_version_from_file(fp)
            index['version'] = version
            index['endian'] = endian
            index['records'] = {}
            index['indexes'] = {}
            index['parts'] = {}
            PIP = {} # parts in process
            PN = 1
            
            TS2ID = utils.ts_to_id(version)
            
            if self.progress:
                description = "Indexing STDF file '%s'" % os.path.split(fp)[1]
                index_progress = tqdm(total=os.path.getsize(fp), ascii=True, disable=not self.progress, desc=description, leave=False, unit='b')

            for _, REC_TYP, REC_SUB, REC in utils.check_records_from_file(fp):
                REC_ID = TS2ID[(REC_TYP, REC_SUB)]
                REC_LEN = len(REC)
                if REC_ID not in index['records']: index['records'][REC_ID] = []
                index['indexes'][offset] = (REC, REC_ID)
                index['records'][REC_ID].append(offset)
                if REC_ID in ['PIR', 'PRR', 'PTR', 'FTR', 'MPR']:
                    if REC_ID == 'PIR':
                        pir_HEAD_NUM, pir_SITE_NUM = self._get_head_and_site_num("PIR", REC)
                        if (pir_HEAD_NUM, pir_SITE_NUM) in PIP:
                            raise Exception("One should not be able to reach this point !")
                        PIP[(pir_HEAD_NUM, pir_SITE_NUM)] = PN
                        index['parts'][PN]=[]
                        index['parts'][PN].append(offset)
                        PN+=1
                    elif REC_ID == 'PRR':
                        prr_HEAD_NUM, prr_SITE_NUM = self._get_head_and_site_num("PRR", REC)
                        if (prr_HEAD_NUM, prr_SITE_NUM) not in PIP:
                            raise Exception("One should not be able to reach this point!")
                        pn = PIP[(prr_HEAD_NUM, prr_SITE_NUM)]
                        index['parts'][pn].append(offset)
                        del PIP[(prr_HEAD_NUM, prr_SITE_NUM)]
                    elif REC_ID == 'PTR':
                        ptr_HEAD_NUM, ptr_SITE_NUM = self._get_head_and_site_num("PTR", REC)
                        if (ptr_HEAD_NUM, ptr_SITE_NUM) not in PIP:
                            raise Exception("One should not be able to reach this point!")
                        pn = PIP[(ptr_HEAD_NUM, ptr_SITE_NUM)]
                        index['parts'][pn].append(offset)
                    elif REC_ID == 'FTR':
                        ftr_HEAD_NUM, ftr_SITE_NUM = self._get_head_and_site_num("FTR", REC)
                        if (ftr_HEAD_NUM, ftr_SITE_NUM) not in PIP:
                            raise Exception("One should not be able to reach this point!")
                        pn = PIP[(ftr_HEAD_NUM, ftr_SITE_NUM)]
                        index['parts'][pn].append(offset)
                    elif REC_ID == 'MPR':
                        mpr_HEAD_NUM, mpr_SITE_NUM = self._get_head_and_site_num("MPR", REC)
                        if (mpr_HEAD_NUM, mpr_SITE_NUM) not in PIP:
                            raise Exception("One should not be able to reach this point!")
                        pn = PIP[(mpr_HEAD_NUM, mpr_SITE_NUM)]
                        index['parts'][pn].append(offset)
                    else:
                        raise Exception("One should not be able to reach this point! (%s)" % REC_ID)
                if self.progress: index_progress.update(REC_LEN)
                offset += REC_LEN
        return index
    
    def print_index(self):
        print("~~~~~~~~~~~~~~~~~~~~ Records ~~~~~~~~~~~~~~~~~~~~")
        for rec_id, offsets in self.index['records'].items():
            print(f"{rec_id} count: {len(offsets)}")
        print("~~~~~~~~~~~~~~~~~~~~ Parts ~~~~~~~~~~~~~~~~~~~~")
        part_count = len(list(self.index['parts'].keys()))
        print(f"Part count: {part_count}")
        for pid, offsets in self.index['parts'].items():
            print(f"part {pid} record count: {len(offsets)}")
        print("~~~~~~~~~~~~~~~~~~~~ Indexes ~~~~~~~~~~~~~~~~~~~~")
        
    
    # if rec_spec is dict, rec_spec[rec_id] = [rec_index1, rec_index2, ...]
    def get_rec_objects(self, rec_spec):
        if isinstance(rec_spec, dict):
            rec_objects = {}
            for rec_id in rec_spec:
                rec_objects[rec_id] = {}
                if not rec_spec[rec_id]:
                    for offset in self.index['records'][rec_id]:
                        rec, _ = self.index['indexes'][offset]
                        rec_objects[rec_id][offset] = utils.create_record_object(self.index['version'], self.index['endian'], rec_id, rec)
                else:
                    for i in rec_spec[rec_id]:
                        offset = self.index['records'][rec_id][i]
                        rec, _ = self.index['indexes'][offset]
                        rec_objects[rec_id][offset] = utils.create_record_object(self.index['version'], self.index['endian'], rec_id, rec)
            
            # if len(rec_objects.keys()) == 1:        
            #     rec_id = list(rec_objects.keys())[0]
            #     rec_objects = rec_objects[rec_id]
        else:
            Exception(f"invalid type(rec_spec) = {type(rec_spec)}")
            
        
        return rec_objects
        
    def _get_test_num_nam_dict(self):
        TEST_NUM_NAM = {}
        if 'TSR' not in self.index['records']:
            print("(WARNING) No test synopsis records (TSRs) in STDF file. This might be because input file is partial file.")
            return TEST_NUM_NAM
        for tsr_offset in self.index['records']['TSR']:
            tsr = TSR(self.index['version'], self.index['endian'], self.index['indexes'][tsr_offset][0])
            TEST_NUM = tsr.get_value('TEST_NUM')
            TEST_NAM = tsr.get_value('TEST_NAM')
            TEST_TYP = tsr.get_value('TEST_TYP').upper()
            if TEST_NUM not in TEST_NUM_NAM:
                TEST_NUM_NAM[TEST_NUM] = []
            if (TEST_NAM, TEST_TYP) not in TEST_NUM_NAM[TEST_NUM]:
                TEST_NUM_NAM[TEST_NUM].append((TEST_NAM, TEST_TYP))
        return TEST_NUM_NAM
    
    def _get_head_and_site_num(self, rec_id, rec):
        '''
            fast method to return head num and site num from raw bytes
        '''
        if rec_id in ["PRR", "PIR"]:
            head_num = struct.unpack('b', rec[4:5])[0]
            site_num = struct.unpack('b', rec[5:6])[0]
        elif rec_id in ["FTR", "PTR", "MPR"]:
            head_num = struct.unpack('b', rec[8:9])[0]
            site_num = struct.unpack('b', rec[9:10])[0]
        else:
            raise Exception(f"method can't handle rec_id: {rec_id}")
        return head_num, site_num
    
    # this function is a faster alternative to utils.create_record_object() to PTR's
    # calls to utils.create_record_object() for PTR's is a bottleneck
    def _get_ptr_fields_from_raw_bytes(self, raw_bytes):
        '''
        Parameters
        ----------
        raw_bytes : bytes
            Raw bytes of the paramatric test record (PTR)
            PTR fields are extracted from the raw bytes

        Returns
        -------
        ptr_fields : dict
            dictionary of fields extracted from the PTR

        '''
        ptr_fields = {}
        ptr_fields['TEST_NUM'] = struct.unpack('I', raw_bytes[4:8])[0]
        num_chars = struct.unpack('b', raw_bytes[16:17])[0]
        ptr_fields['TEST_TXT'] = raw_bytes[17:17+num_chars].decode("utf-8")
        ptr_fields['TEST_FLG'] = self._byte_to_bit_arr(raw_bytes[10])
        ptr_fields['RESULT'] = struct.unpack('f', raw_bytes[12:16])[0]
        return ptr_fields
    
    def _get_bmap(self, mode="sw_bins"):
        '''
            PARAMETERS
            ----------
            mode : string ('hw_bins' or 'sw_bins')
            determines if bin map contains SW bins of HW bins
            
            RETURNS
            -------
            bmap : dict
            contains {part_id (string) : bin# (int)} pairs
        '''
        bmap = {}
        version = self.index['version']
        endian = self.index['endian']
        # print("(DEBUG) PRR count:", len(self.index['records']['PRR']))
        for index in self.index['records']['PRR']:
            rec, rec_id = self.index['indexes'][index]
            rec_obj = utils.create_record_object(version, endian, rec_id, rec)
            if mode == 'hw_bins':
                bin_num = rec_obj.get_fields("HARD_BIN")[3]
            if mode == 'sw_bins':
                bin_num = rec_obj.get_fields("SOFT_BIN")[3]
            part_id = rec_obj.get_fields("PART_ID")[3]
            # print("(DEBUG) part_id:", part_id)
            bmap[part_id] = bin_num
        # print("(DEBUG) bmap:", bmap)
        return bmap
    
    # get bin counts based on PRR's   
    # mode can be ['hw_bins','sw_bins']        
    def _get_bin_cnts(self, mode):
        bin_cnts = {}
        bmap = self._get_bmap(mode)
        for bin_num in bmap.values():
            if bin_num not in bin_cnts:
                bin_cnts[bin_num] = 0
            bin_cnts[bin_num] += 1
        return bin_cnts
    
    # update SBR bin counts based on PRR's
    # if SBR/HBR does not exist for a geiven bin code, a new record is inserted
    # mode can be ['hw_bins','sw_bins']
    def _update_bin_cnts(self, mode):
        version = self.index['version']
        endian = self.index['endian']
        assert mode in ['hw_bins', 'sw_bins'], f"invalid mode: {mode}"
        bin_cnts = self._get_bin_cnts(mode)
        print("(DEBUG) bin_cnts:", bin_cnts)
        rec_id = 'SBR' if mode == 'sw_bins' else 'HBR'
        bin_num_key = 'SBIN_NUM' if mode == 'sw_bins' else 'HBIN_NUM'
        bin_nam_key = 'SBIN_NAM' if mode == 'sw_bins' else 'HBIN_NAM'
        bin_cnt_key = 'SBIN_CNT' if mode == 'sw_bins' else 'HBIN_CNT'
        
        # if SBR/HBR does not exist for bin code, insert a new record
        # for bin_num, bin_cnt in bin_cnts.items():
        #     rec_objects = self.get_rec_objects({rec_id : []})
        #     bin_numbers = []
        #     for rec_obj in rec_objects.values():
        #         bin_numbers.append(rec_obj.get_value(bin_num_key))
        #         if bin_num not in bin_numbers:
        #             new_rec_obj = SBR(version, endian) if mode == 'sw_bins' else HBR(version, endian)
        #             new_rec_obj.set_value(bin_num_key, bin_num)
        #             new_rec_obj.set_value(bin_nam_key, bin_num)
        #             new_rec_obj.set_value(bin_num_key, bin_num)
                    
        for index in self.index['records'][rec_id]:
            rec, rec_id = self.index['indexes'][index]
            rec_obj = utils.create_record_object(version, endian, rec_id, rec)
            bin_num = rec_obj.get_fields(bin_num_key)[3]
            bin_nam = rec_obj.get_fields(bin_nam_key)[3]
            bin_cnt = rec_obj.get_fields(bin_cnt_key)[3]
            if bin_cnt != bin_cnts[bin_num]:
                print(f"(DEBUG) updating {rec_id} bin# {bin_num} ({bin_nam}) bin count ({bin_cnt} -> {bin_cnts[bin_num]})")
            assert bin_cnts[bin_num], \
                "no dict value for (bin# {bin_num}, {bin_nam}) in bin_cnts"
            rec_obj.set_value(bin_cnt_key, bin_cnts[bin_num])
            rec = rec_obj.__repr__()
            self.index['indexes'][index] = (rec, rec_id)
    
    # mode option can be ['total', 'pass', 'retest']
    def _update_part_cnt(self, mode):
        assert mode in ['total', 'pass', 'retest'], f"invalid mode: '{mode}'"
        version = self.index['version']
        endian = self.index['endian']
        
        if mode == 'total':
            cnt = self.get_total_part_cnt()
        if mode == 'pass':
            cnt = self.get_pass_part_cnt()
        if mode == 'retest':
            cnt = self.get_retest_part_cnt()
            
        for index in self.index['records']['PCR'] + self.index['records']['WRR']:
            rec, rec_id = self.index['indexes'][index]  
            rec_obj = utils.create_record_object(version, endian, rec_id, rec)
            if mode == 'total':
                rec_obj.set_value("PART_CNT", cnt)
            if mode == 'pass':
                rec_obj.set_value("GOOD_CNT", cnt)
            if mode == 'retest':
                rec_obj.set_value("RTST_CNT", cnt)
            rec = rec_obj.__repr__()
            self.index['indexes'][index] = (rec, rec_id)
            
    def _byte_to_bit_arr(self, raw_byte):
        bit_arr = ['0'] * 8
        for i in range(8):
            mask = 2**i
            if (mask & raw_byte) == mask:
                bit_arr[i] = '1'
        return bit_arr
    
    def _limit_size(self, val):
        val = val if val < self.MAX_4BYTE_FLOAT else self.MAX_4BYTE_FLOAT-1
        val = val if val > self.MIN_4BYTE_FLOAT else self.MIN_4BYTE_FLOAT+1
        return val
            
    #### ~~~~~ Public Methods ~~~~~ ####        
            
    def write_stdf(self, fp, overwrite=True):
        if not overwrite:
            assert not os.path.isfile(fp), f"File already exists: {fp}"
        with open(fp, "wb") as stdf_file:
            idx_rec_list = list(self.index['indexes'].items())
            idx_rec_list = sorted(idx_rec_list) # sort ascending by index
            for _, (rec, rec_id) in idx_rec_list:
                stdf_file.write(rec)
                
    def update_total_part_count(self):
        self._update_part_cnt('total')
                
    def update_pass_part_count(self):
        self._update_part_cnt('pass')
        
    def update_retest_part_count(self):
        self._update_part_cnt('retest')
        
    def get_total_part_cnt(self):
        return len(self._get_bmap())
    
    def get_pass_part_cnt(self):
        bmap = self._get_bmap()
        cnt = 0
        for sbin_num in bmap.values():
            if sbin_num == 1:
                cnt += 1
        return cnt
    
    def get_retest_part_cnt(self):
        total_part_cnt = len(self._get_bmap())
        prr_cnt = len(self.index['records']['PRR'])
        return prr_cnt - total_part_cnt
    
    def update_sbin_cnts(self):
        self._update_bin_cnts('sw_bins')
    
    def update_hbin_cnts(self):
        self._update_bin_cnts('hw_bins')
    
    def get_sbin_cnts(self):
        return self._get_bin_cnts('sw_bins')
    
    def get_hbin_cnts(self):
        return self._get_bin_cnts('hw_bins')

    def is_part_pass(self, part_flag):
        if part_flag[-5] == '1':
            print("(DEBUG) part flag bit 5=1, indicating p/f status is invalid. Checking p/f bit anyway...")
        if part_flag[-4] == '0': 
            return True
        else:
            return False
        
    # not tested
    def is_part_superceding(self, part_flag, mode="xy"):
        '''
        Parameters
        ----------
        part_flag : array[8] of strings '1' or '0'
            PART_FLG field of part result record (PRR).
        mode : string, optional
            The default is "xy", options are ["xy", "part_id"].
            If mode is "part_id" method returns True if bit 0 is set
            If mode is "xy" method returns True if bit 1 is set

        Returns
        -------
        bool
            Indicates if part sequence superceds any previous part sequence 
            with the same part_id or (x,y).
        '''
        assert not (part_flag[-1] == '1' and part_flag[-2] == '1'), \
            "part flag bit 0 and bit 1 both set, but only 1 or the other bits should be set"
        if part_flag[-1] == '1' or part_flag[-2] == '1': 
            return True
        else:
            return False
        
    def is_test_pass(self, test_flag):
        
        # assert test_flag[-7] == '1', "part flag pass/fail bit is invalid"
        if test_flag[-8] == '0': 
            return True
        else:
            return False

    def set_part_flag_pf_bit(self, part_flag, is_pass=True):
        '''
            is_pass : can be True or False
        '''
        assert isinstance(is_pass, bool), "is_pass must be boolean (True or False)"
        if part_flag[-5] == '1':
            print("(DEBUG) part flag bit 5=1, indicating p/f status is invalid. Updating p/f bit anyway...")
        if is_pass:
            part_flag[-4] = '0'
        else:
            part_flag[-4] = '1'
        return part_flag
    
    # not tested
    def set_part_flag_supercede_bit(self, part_flag, is_superceding=True, mode='xy'):
        '''
        Parameters
        ----------
        is_superceding : bool
            True if part sequence supercedes any previous part sequence with
            the same (x,y) or part_id
        part_flag : array[8] of strings '1' or '0'
            PART_FLG field of part result record (PRR).
        mode : string, optional
            The default is "xy", options are ["xy", "part_id"].
            If mode is "part_id" method returns True if bit 1 is set
            If mode is "xy" method returns True if bit 2 is set

        Returns
        -------
        part_flag : array[8] or strings '1' or '0'
            updated part_flag
        '''
        assert mode in ['xy', 'part_id'], f"mode must be 'xy' or 'FT', mode '{mode}' is invalid"
        assert isinstance(is_superceding, bool), "'is_retest' must be boolean (True or False)"
        set_idx = -2 if mode == 'xy' else -1
        if is_superceding:
            check_idx = -2 if mode == 'part_id' else -1
            assert part_flag[check_idx] != '1', "attempted to set both part_id and xy retest bits. Only 1 should be set."    
            part_flag[set_idx] = '1'
        else:
            part_flag[set_idx] = '0'
        return part_flag
    
    def get_last_part_id(self):
        return max([part_id for part_id in self.index['parts'].keys()])
    
    def set_test_flag_pf_bit(self, test_flag, is_pass=True):
        '''
            'is_pass' is bool
        '''
        assert isinstance(is_pass, bool), "is_pass must be boolean (True or False)"
        if is_pass:
            test_flag[-8] = '0'
        else:
            test_flag[-8] = '1'
        return test_flag
    
    def get_test_data(self, tnum_tnam = [], part_ids = []):
        '''
        !!! does not handle FTR (yet)
        Parameters
        ----------
        tnum_tnam : list of tuples, optional
            List of (tnum,tnam) corresponding to TSRs to update. If empty update all TSR
            
        part_ids : list of string
            Part IDs to get results of
            
        Returns
        -------
        data : dict
            {
                (tnum,tnam) : [
                        {'val' : <float>, 'is_pass' : <bool>, 'part_id' : <string>}, ...
                ], ...
            }
            
        '''
        data = {}
        version = self.index['version']
        endian = self.index['endian']
        for index_list in self.index['parts'].values():
            prr_index = index_list[-1]
            prr_rec, prr_rec_id = self.index["indexes"][prr_index]
            rec_obj = utils.create_record_object(version, endian, prr_rec_id, prr_rec)
            part_id = rec_obj.get_fields('PART_ID')[3]
            if part_id in part_ids or not part_ids:
                for index in index_list:
                    rec, rec_id = self.index['indexes'][index]
                    if rec_id == 'PTR':
                        ptr_fields = self._get_ptr_fields_from_raw_bytes(rec)
                        tnum = ptr_fields['TEST_NUM']
                        tnam = ptr_fields['TEST_TXT']
                        if (tnum,tnam) in tnum_tnam or not tnum_tnam:
                            if (tnum,tnam) not in data:
                                data[(tnum,tnam)] = []
                            data[(tnum,tnam)].append({
                                'val' : ptr_fields['RESULT'],
                                'is_pass' : self.is_test_pass(ptr_fields['TEST_FLG']),
                                'part_id' : part_id
                                })
        return data
    
    def update_tsr(self, tnum_tnam = [], allow_add_dup_tnum = False):
        '''
        TODO: Add new TSR if TSR does not exist
        TODO: *handle FTR,MPR
        tnum_tnam : list of tuples, optional
            List of (tnum,tnam) corresponding to TSRs to update. If empty update all TSR
        allow_add_dup_tnum : bool, optional
            Flag weather to allow multiple TSR for the same test number but different test name.
            Duplicate test number TSR's cause some STDF readers to throw errors
        
        Updates test synopsis records (TSR) based on PTR's and *FTR's
        for each (tnum,tnam) in data, if tsr exists with matching (tnum,tnam) update record,
        if tsr does not exist and no dup tnum exists, create new record, 
        or if dup tnum exists and allow_dup_tnum=True, create new record
        
        '''
        # self.test_num_name_dict = self._get_test_num_nam_dict()
        data = self.get_test_data(tnum_tnam=tnum_tnam)
        version = self.index['version']
        endian = self.index['endian']
        updated_tsr = []
        for index in self.index['records']['TSR']:
            rec = self.index['indexes'][index][0]
            rec_obj = utils.create_record_object(version, endian, 'TSR', rec)
            tnum = rec_obj.get_fields('TEST_NUM')[3]
            tnam = rec_obj.get_fields('TEST_NAM')[3]
            if (tnum,tnam) in tnum_tnam or not tnum_tnam:
                ptr_dict_list = data[(tnum, tnam)]
                val_list = [dict_['val'] for dict_ in ptr_dict_list]
                is_pass_list = [dict_['is_pass'] for dict_ in ptr_dict_list]
                
                rec_obj.set_value('TEST_MIN', self._limit_size(min(val_list)))
                rec_obj.set_value('TEST_MAX', self._limit_size(max(val_list)))
                rec_obj.set_value('TST_SUMS', self._limit_size(sum(val_list)))
                test_mean = statistics.mean(val_list)
                test_sqrs = self._limit_size(sum([(x - test_mean)**2 for x in val_list]))
                rec_obj.set_value('TST_SQRS', test_sqrs)
                rec_obj.set_value('EXEC_CNT', len(is_pass_list))
                rec_obj.set_value('FAIL_CNT', len(is_pass_list) - sum(is_pass_list))
                
                print(f"(DEBUG) Updated TSR {tnum} {tnam}")
                rec = rec_obj.__repr__()
                self.index['indexes'][index] = (rec, 'TSR')
                updated_tsr.append(tnum,tnam)
        
        # Add TSR if it doesn't exist
        # for (tnum,tnam) in data:
        #     is_update_target = True if (tnum,tnam) in tnum_tnam or not tnum_tnam else False
        #     is_updated = True if (tnum,tnam) not in updated_tsr else False
        #     if not is_updated and is_update_target:
        #         rec_obj = create
        
    
    def insert_record(self, rec, rec_id, index):
        '''
        updates stdf index to accomodate new record
            1) 'records': for each index, if index > new_index, increment index by rec_len
            2) 'parts': for each index, if index > new_index, increment index by rec_len
            3) 'indexes': for each index, if key > index, increment key by rec_len 
        '''
        assert index in list(self.index['indexes'].keys()), f"no matching index in stdf object (index: {index})"
        rec_len = len(rec)
        
        # Shift up record indexes above insertion point
        for rec_id_ in self.index['records']:
            for i, index_ in enumerate(self.index['records'][rec_id_]):
                if index_ >= index:
                    self.index['records'][rec_id_][i] += rec_len
        
        # Insert new record index to records dict
        if rec_id not in self.index['records']:
            self.index['records'][rec_id] = []
        i = bisect.bisect_left(self.index['records'][rec_id], index)
        self.index['records'][rec_id].insert(i, index)
        
        # Shift up parts record indexes above insertion point
        for part_id_ in self.index['parts']:
            for i, index_ in enumerate(self.index['parts'][part_id_]):
                if index_ >= index:
                    self.index['parts'][part_id_][i] += rec_len
                    
        # if record is part sequence record, 
        # insert new record index into parts dict
        for part_id_ in self.index['parts']:
            start_idx = self.index['parts'][part_id_][0]
            stop_idx = self.index['parts'][part_id_][-1]
            if index > start_idx and index <= stop_idx:
                i = bisect.bisect_left(self.index['parts'][part_id_], index)
                self.index['parts'][part_id_].insert(i, index)
        
        updated_dict = {}
        for index_, val in self.index['indexes'].items():
            if index_ >= index:
                updated_dict[index_ + rec_len] = val
            else:
                updated_dict[index_] = val
        updated_dict[index] = (rec, rec_id)
        
        self.index['indexes'] = updated_dict
    
    
    # contiguous insertion of multiple records
    # (not fully tested)
    def insert_records(self, recs, index, is_new_part_seq=False):
        '''
        updates stdf index to accomodate new records

        Parameters
        ----------
        recs : [(<raw_rec_bytes>, <rec_id>)]
            Array of tuples with raw record bytes and rec ID string.
            Each array element is a record to insert
            Records are inserted sequentially starting at 'index'
        index : integer
            Records will be inserted *before* this index.
        is_new_part_seq : bool
            Whether 'recs' consists of a complete new part sequence
            This is an edge case

        Returns
        -------
        None.

        '''
        
        assert index in list(self.index['indexes'].keys()), f"no matching index in stdf object (index: {index})"
        
        length = 0
        for rec, _ in recs:
            length += len(rec)
           
        # Shift up record indexes above insertion point
        for rec_id_ in self.index['records']:
            for i, index_ in enumerate(self.index['records'][rec_id_]):
                if index_ >= index:
                    self.index['records'][rec_id_][i] += length
        
        # Insert new record indexes to records dict
        index_ = index
        for rec, rec_id in recs:
            if rec_id not in self.index['records']:
                self.index['records'][rec_id] = []
            i = bisect.bisect_left(self.index['records'][rec_id], index_)
            self.index['records'][rec_id].insert(i, index_)
            index_ += len(rec)
            
        # Shift up parts record indexes above insertion point            
        for part_id_ in self.index['parts']:
            for i, index_ in enumerate(self.index['parts'][part_id_]):
                if index_ >= index:
                    self.index['parts'][part_id_][i] += length
        
        # if records is part sequence record, 
        # insert new record indexes into parts dict
        index_ = index
        if not is_new_part_seq:
            for part_id_ in self.index['parts']:
                start_idx = self.index['parts'][part_id_][0]
                stop_idx = self.index['parts'][part_id_][-1]
                if index > start_idx and index <= stop_idx:
                    for rec, rec_id in recs:
                        i = bisect.bisect_left(self.index['parts'][part_id_], index_)
                        self.index['parts'][part_id_].insert(i, index_)
                        index_ += len(rec)
        elif is_new_part_seq:
            found_part_id = False
            if index < self.index['parts'][1][0]: # If index is before first part sequence
                found_part_id = True
                part_id = 1
            last_part_id = self.get_last_part_id()
            if index > self.index['parts'][last_part_id][-1]: # If index is after last part sequence
                found_part_id = True
                part_id = last_part_id
            for part_id_ in self.index['parts']:
                start_idx = self.index['parts'][part_id_][0]
                stop_idx = self.index['parts'][part_id_][-1]
                assert index <= start_idx or index > stop_idx, \
                    "new part sequence cannot be inserted inside existing part sequence"
                if index == start_idx:
                    found_part_id = True
                    part_id = part_id_
            assert found_part_id, "Could not find part ID for new part sequence"
            # Update existing part IDs
            for key in sorted(self.index['parts'].keys(), reverse=True):
                if key >= part_id:
                    self.index['parts'][key+1] = self.index['parts'][key]
            self.index['parts'][part_id] = []
            
            for rec, rec_id in recs:
                self.index['parts'][part_id].append(index_)
                index_ += len(rec)
        
        # Update record index 
        updated_dict = {}
        for index_, val in self.index['indexes'].items():
            if index_ >= index:
                updated_dict[index_ + length] = val
            else:
                updated_dict[index_] = val
        
        index_ = index
        for rec, rec_id in recs:
            updated_dict[index_] = (rec, rec_id)
            index_ += len(rec)
            
        self.index['indexes'] = updated_dict
                
        
if __name__ == "__main__":
    # fp = r'C:/Users/dkane/OneDrive - Presto Engineering/Documents/python_scripts/semi ate stdf processing/stdf file/test files/123456_25_9_25_9__20230531_152904.stdf'
    # fp = r'C:/Users/dkane/OneDrive - Presto Engineering/Documents/python_scripts/semi ate stdf processing/stdf file/test files/5AIY1401-P125_072023.std'
    # fp = r'C:/Users/dkane/OneDrive - Presto Engineering/Documents/python_scripts/semi ate stdf processing/stdf file/test files/G4_MZMD15163_N19347.1_01_20230525.stdf'
    # fp = r'C:/Users/dkane/OneDrive - Presto Engineering/Documents/python_scripts/semi ate stdf processing/stdf file/test files/G4_TIA25133_N19347.1_01_20230530.stdf'
    
    # fp = r'C:/Users/dkane/OneDrive - Presto Engineering/Documents/Integra-Job/SEAKR/Portico/8DMX09001/Portico_8DMX09001_03_P1_25C_20230905_114011.stdf'
    fp = r"C:/Users/dkane/OneDrive - Presto Engineering/Documents/Integra-Job/SEAKR/Portico/8DMX09001/Wafer 04 Pass 2 0C 10-11-2023 manual test/Portico_8DMX09001_04_P2_0C_20231011_162055.stdf"
    
    # get indexed stdf file
    stdf = STDFFile(fp, progress = True)
    
    dt0 = datetime.now()

    stdf.print_index()

    dt1 = datetime.now()
    delta = timedelta()
    delta = dt1 - dt0
    print("End time: ", dt1)
    print("Elapsed time: ", delta)  