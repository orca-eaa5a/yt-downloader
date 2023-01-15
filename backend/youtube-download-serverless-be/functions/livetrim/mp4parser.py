import logging
import subprocess
import json
import copy
from pymp4.parser import Box
from pymp4.util import BoxUtil

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class PyMp4Wrapper(object):
    def __init__(self) -> None:
        self.ftyp = None
        self.moov = None
        self.mdat = None
        self.raw = None
        self.sample_arr = {
            'video_track': [],
            'sound_track': [],
        }
        self.chunk_arr = {
            'video_track': [],
            'sound_track': [],
        }
        self.video_track = None
        self.media_track = None
        pass

    def set_binary(self, binary:bytes):
        if not binary:
            logging.error('[set_binary] null binary')
            assert 0
        self.raw =binary
        pass

    def get_moov_size(self):
        if not self.raw:
            logging.error('[get_moov_size] null binary')
            assert 0
        
        if not self.ftyp:
            self.ftyp = Box.parse(self.raw)
        return int.from_bytes(self.raw[self.ftyp.end:self.ftyp.end+4], byteorder='big')

    def parse(self):
        try:
            self.ftyp = Box.parse(self.raw)
            self.moov = Box.parse(self.raw[self.ftyp.end:])
            # parse_test = Box.parse(self.raw[
            #     BoxUtil.first(self.moov, b'stco').end+self.ftyp.end : 
            #     ])
        except OSError as e:
            logging.error('[parse] invalid mp4 format binary or moov header is not located in front of the mdat')
            assert 0
        self.mdat = self.raw[self.moov.end:]

        # set track
        track_list = list(BoxUtil.find(self.moov, b'trak'))
        for trak in track_list:
            if BoxUtil.first(trak, b'hdlr').handler_type == b'vide':
                self.video_track = trak
            else:
                self.sound_track = trak

        self.make_chunk_arr('video_track')
        self.make_chunk_arr('sound_track')


    def get_running_time(self, track='video_track'):
        track_duration = BoxUtil.first(getattr(self, track), b'mdhd').duration
        track_timescale = BoxUtil.first(getattr(self, track), b'mdhd').timescale

        return int(track_duration/track_timescale)

    def get_chunk_arr(self, track='video_track'):
        return getattr(self, 'chunk_arr')[track]
    
    def get_sample_arr(self, track='video_track'):
        return getattr(self, 'sample_arr')[track]

    def get_chunk_count(self, track='video_track'):
        return BoxUtil.first(getattr(self, track), b'stco').entry_count

    def get_chunk_info_arr(self, track='video_track'):
        return BoxUtil.first(getattr(self, track), b'stsc').entries
    
    def get_chunk_offset_arr(self, track='video_track'):
        return BoxUtil.first(getattr(self, track), b'stco').entries

    def get_sample_size_arr(self, track='video_track'):
        return BoxUtil.first(getattr(self, track), b'stsz').entry_sizes
    
    def get_compostion_arr(self, track='video_track'):
        return BoxUtil.first(getattr(self, track), b'ctts').entry_sizes

    def get_sample_atom_arr(self, track='video_track'):
        return BoxUtil.first(getattr(self, track), b'stts').entries
    
    def get_sync_sample_arr(self):
        return BoxUtil.first(getattr(self, 'video_track'), b'stss').entries

    def make_chunk_arr(self, track='video_track'):
        # chunk timestamp, chunk offset, chunk size number_of_samples, prev_sample_count
        chunk_info_arr = self.get_chunk_info_arr(track)
        sample_size_arr = self.get_sample_size_arr(track)
        chunk_offset_arr = self.get_chunk_offset_arr(track)
        sample_per_sec_arr = self.get_samples_per_sec_arr(track)

        chunk_info_arr_idx = 0
        sample_per_sec_arr_idx = 0
        sample_count = 0
        timestamp = 0
        next_chunk_info = None
        for chunk_idx in range(len(chunk_offset_arr)):
            try:
                if not next_chunk_info:
                    next_chunk_info = chunk_info_arr[chunk_info_arr_idx+1]
                if next_chunk_info['first_chunk'] == chunk_idx+1:
                    chunk_info_arr_idx += 1
                    next_chunk_info = chunk_info_arr[chunk_info_arr_idx+1]
            except IndexError as ie:
                next_chunk_info = None
                pass
            finally:
                cur_chunk_info = chunk_info_arr[chunk_info_arr_idx]
            chunk_size = 0
            for i in range(cur_chunk_info['samples_per_chunk']):
                self.sample_arr[track].append(
                    {
                        'chunk_idx':  chunk_idx,
                        'sample_idx': sample_count,
                        'sample_offset': chunk_offset_arr[chunk_idx].chunk_offset + chunk_size, 
                        'sample_size': sample_size_arr[sample_count]
                    }
                )
                chunk_size += sample_size_arr[sample_count]
                sample_count += 1
            base_sample_index = sample_count - cur_chunk_info['samples_per_chunk']
            if base_sample_index > sample_per_sec_arr[sample_per_sec_arr_idx]['sample_count']:
                sample_per_sec_arr_idx+=1
            
            timestamp = base_sample_index/sample_per_sec_arr[sample_per_sec_arr_idx]['samples_per_sec']

            self.chunk_arr[track].append({
                'chunk_idx': chunk_idx,
                'chunk_offset': chunk_offset_arr[chunk_idx].chunk_offset,
                'start_sample_idx': base_sample_index,
                'number_of_samples': cur_chunk_info['samples_per_chunk'],
                'chunk_size': chunk_size,
                'timestamp': timestamp
            })

    def get_samples_per_sec_arr(self, track='video_track'):
        """
        동영상 1초 몇개의 sample이 필요한지 계산
        ret:
        [
            {
                'sample_count'
                'duration' # second
                'sample_delta'
            },
            ...
        ]
        """
        ret = []
        track_sample_atom_arr = self.get_sample_atom_arr(track)
        track_duration = BoxUtil.first(getattr(self, track), b'mdhd').duration
        track_timescale = BoxUtil.first(getattr(self, track), b'mdhd').timescale
        for atom in track_sample_atom_arr:
            if atom and track_duration <= 0:
                logger.error('[get_sample_count_per_sec] : 뭔가 잘못 됨')
                assert False

            if track_duration < atom['sample_count'] * atom['sample_delta']:
                break
            else:
                ret.append(
                    {
                        'sample_count': atom['sample_count'],
                        'sample_delta': atom['sample_delta'],
                        'samples_per_sec': int(track_timescale / atom['sample_delta']),
                        'duration': int((atom['sample_count'] * atom['sample_delta'])/track_timescale)
                    }
                )
                track_duration -= atom['sample_count'] * atom['sample_delta']

        return ret

    def get_chunk_by_sample_index(self, sample_index, track='video_track'):
        """
        sample_index를 기반으로, sample이 포함된 chunk를 가져옵니다.
        ! sample_index는 0부터 시작합니다.

        ret:
        
        """
        for chunk_i in self.get_chunk_arr(track):
            if chunk_i['start_sample_idx'] <= sample_index and sample_index < chunk_i['start_sample_idx'] + chunk_i['number_of_samples']:
                return chunk_i
        logging.error('[get_chunk_by_sample_index] invalid index')
        assert False

    def get_chunk_by_index(self, index, track='video_track'):
        """
        desc:
        index에 맞는 chunk를 가져옵니다.
        ! index는 1부터 시작합니다

        ret:
        'chunk_idx': chunk_idx,
        'chunk_offset': start file offset of chunk
        'start_sample_idx': start offset of sample in chunk
        'number_of_samples': number of samples that chunk contained
        'chunk_size': chunk_size,
        'timestamp': timestamp of video that chunk coresspond
        """
        try:
            return self.get_chunk_arr(track)[index]
        except IndexError as ie:
            logging.error('[get_chunk_by_index] invalid index')
        assert False

    def get_chunk_by_time(self, timestamp, track='video_track', sync=False):
        """
        desc:
        시간 값에 맞는 chunk를 가져옵니다.
        시간 값에 해당하는 sample이 chunk의 시작 sample이 아닐 경우,
        chunk의 시작 sample을 가져옵니다.
        ! millisecond는 무시합니다
        sync:
        iframe을 고려하여 chunk를 가져옵니다.
        요청한 chunk의 timestamp를 기준으로 선행하는 chunk 중, iframe을 포함하는 chunk를 return합니다. 

        ret:
        chunk_arr info
        """
        
        done = False
        chunk_arr = self.get_chunk_arr(track)
        prev_chunk_i = chunk_arr[0]
        idx = 0
        sync_sample_arr = self.get_sync_sample_arr()
        candidate_chunks = []
        for chunk_i in chunk_arr:
            prev_chunk_i = chunk_i
            if sync:
                for sync_sample in sync_sample_arr:
                    if chunk_i['timestamp'] <= timestamp and \
                        chunk_i['start_sample_idx'] <= sync_sample.sample_number < chunk_i['start_sample_idx'] + chunk_i['number_of_samples']:
                        candidate_chunks.append(chunk_i)
            if chunk_i['timestamp'] >= timestamp:
                done = True
                break

        if timestamp != 0 and not done:
            logger.error('[get_chunk_by_time] : timestamp is not in duration')
            assert False
        if sync:
            return candidate_chunks[-1], prev_chunk_i
        return prev_chunk_i, None

    def get_chunk_by_offset(self, offset, track='video_track'):
        """
        desc:
        offset에 맞는 chunk를 가져옵니다.
        offset에 해당하는 sample이 chunk의 시작 sample이 아닐 경우,
        chunk의 시작 sample을 가져옵니다.

        ret:
        chunk_offset, chunk_size, samples_per_chunk
        """
        done = False
        chunk_arr = self.get_chunk_arr(track)
        prev_chunk_i = chunk_arr[0]
        for chunk_i in chunk_arr:
            if chunk_i['chunk_offset'] > offset:
                done = True
                break
        if not done:
            logger.error('[get_chunk_by_offset] : invalid offset')
            assert False
        
        return prev_chunk_i

    def get_sample_by_index(self, index, track='video_track'):
        """
        desc:
        index에 맞는 sample을 가져옵니다.

        ret:
        sample_offset, sample_size
        """
        try:
            sample = self.get_sample_arr(track)[index]
        except IndexError as ie:
            logger.error('[get_sample_by_index] : invalid index')
            assert False

        return sample

    def get_sample_by_offset(self, offset, track):
        """
        desc:
        offset에 맞는 sample을 가져옵니다.
        offset이 sample의 시작 지점이 아닐 경우, 범위 내에 offset을 포함하는
        sample을 가져옵니다.

        ret:
        sample_offset, sample_size
        """
        chunk = self.get_chunk_by_offset(offset, track)
        idx = 0
        sample_arr = self.get_sample_arr(track)
        _prev = sample_arr[chunk['start_sample_idx']]
        for sample in sample_arr[chunk['start_sample_idx']:]:
            if chunk['number_of_samples'] == idx:
                logger.error('[get_sample_by_offset] : invalid offset')
                assert False
            idx += 1
            if sample['sample_offset'] > offset:
                return _prev
            _prev = sample
        
        assert False

class MpegTool(object):
    def __init__(self) -> None:
        self.parser = PyMp4Wrapper()
        pass
    
    def get_box_size(self, raw):
        return int.from_bytes(raw[:4], byteorder="big")

    def edit_mvhd_duration(self, moov, duration:int):
        """
        :duration
            - time seconds
        """
        mvhd = BoxUtil.first(moov, b'mvhd')
        mvhd.duration = int(mvhd.timescale * duration)
        pass
    
    def edit_track_duration(self, moov, duration:int, track):
        """
        :duration
            - time seconds
        :track_type
            - video_track, sound_track object
        """
        timescale = BoxUtil.first(moov, b'mvhd').timescale
        tkhd = BoxUtil.first(track, b'tkhd')
        tkhd.duration = int(timescale * duration)

        mdhd = BoxUtil.first(track, b'mdhd')
        mdhd_timescale = mdhd.timescale
        mdhd.duration = int(duration * mdhd_timescale)
        pass
    
    def live_trim(self, url, start_point, end_point, download_cb, sync=True):
        """
        start_timestamp : trim의 시작지점
        duration : trim한 동영상의 running time
        sync : iframe을 고려하여 동영상을 자름

        """
        def edit_stts(self, chunk_s, chunk_e, track):    
            stts = BoxUtil.first(track, b'stts')
            stts_etry = stts.entries
            chunk_start_sample_idx = chunk_s['start_sample_idx']
            chunk_end_sample_idx = chunk_e['start_sample_idx']
            consumed_sample_cnt = chunk_end_sample_idx - chunk_start_sample_idx

            _range = []
            prev = None
            for s in stts_etry:
                if not _range:
                    _range.append([0, s['sample_count']-1])
                    prev = s
                else:
                    _range.append([prev['sample_count'], prev['sample_count'] + s['sample_count']])
            
            # find the chunk started _range
            idx = 0
            for r in _range:
                if r[0] <= chunk_start_sample_idx and chunk_end_sample_idx < r[1]:
                    break
                else:
                    idx += 1
            if idx != 0:
                _range = _range[idx:]
                stts = stts.entries[idx:]
            
            sc = []
            for r in _range:
                n_s = r[1] - r[0] + 1
                if consumed_sample_cnt - n_s < 0:
                    sc.append(consumed_sample_cnt)
                else:
                    sc.append(n_s)
                    consumed_sample_cnt -= n_s
            
            for etry, c in zip(stts.entries, sc):
                etry.sample_count = c

            return stts
        
        def edit_stsc(self, chunk_s, chunk_e, track, track_type):
            stsc = BoxUtil.first(track, b'stsc')
            stsc_etry = stsc.entries
            chunk_start_idx = chunk_s['chunk_idx']
            chunk_end_idx = chunk_e['chunk_idx']
            chunk_info_arr = self.parser.get_chunk_info_arr(track_type)
            _range = []
            idx = 0
            for chunk_info in chunk_info_arr:
                if idx:
                    _range[idx-1]['last_chunk'] = chunk_info['first_chunk']-1
                _range.append({
                        'first_chunk': chunk_info['first_chunk'] - 1,
                        'last_chunk': 0,
                        'samples_per_chunk': chunk_info['samples_per_chunk']
                    })
                idx += 1
            if idx:
                _range[-1]['last_chunk'] = chunk_info['first_chunk']
            
            idx2 = 0
            for r in _range:
                if chunk_end_idx < r['first_chunk']:
                    break
                idx2 += 1
            
            _range = _range[:idx2]
            idx1 = 0
            delta = chunk_start_idx
            for r in _range:
                if r['last_chunk'] - delta > 0:
                    r['first_chunk'] = r['first_chunk'] - delta
                    if r['first_chunk'] < 0:
                        r['first_chunk'] = 0
                    r['last_chunk'] -= delta
                else:
                    idx1 += 1
            _range = _range[idx1:]

            stsc.entries = stsc_etry[idx1:idx2]
            for e, r in zip(stsc.entries, _range):
                e.first_chunk = r['first_chunk']+1

            return stsc

        def edit_stco(self, chunk_s, chunk_e, track, track_type):
            stco = BoxUtil.first(track, b'stco')
            stco.entries = stco.entries[chunk_s['chunk_idx']:chunk_e['chunk_idx']]

            return stco
        
        def edit_stsz(self, chunk_s, chunk_e, track, track_type):
            stsz = BoxUtil.first(track, b'stsz')
            stsz.entry_sizes = stsz.entry_sizes[
                chunk_s['start_sample_idx']:chunk_e['start_sample_idx']
            ]
            stsz.sample_count = len(stsz.entry_sizes)
            return stsz

        def edit_stss(self, chunk_s, chunk_e, track, track_type):
            stss = BoxUtil.first(track, b'stss')            
            stss_etry = stss.entries
            idx1 = 0
            idx2 = 0
            for etry in stss_etry:
                if etry.sample_number < chunk_s['start_sample_idx']:
                    idx1 += 1
                if etry.sample_number > chunk_e['start_sample_idx']:
                    break
                idx2 += 1
            stss.entries = stss.entries[idx1:idx2]
            for etry in stss.entries:
                etry.sample_number -= chunk_s['start_sample_idx']
            

            return stss
        
        def edit_ctts(self, chunk_s, chunk_e, track, track_type):
            ctts = BoxUtil.first(track, b'ctts')            
            sample_count = 0
            idx = 0
            
            for etry in ctts.entries:
                sample_count += etry['sample_count']
                if sample_count > chunk_s['start_sample_idx']:
                    etry.sample_count = sample_count - chunk_s['start_sample_idx']
                    break
                idx+=1
            ctts.entries = ctts.entries[idx:]

            idx=0
            sample_count = 0
            contained_sample = chunk_e['start_sample_idx'] - chunk_s['start_sample_idx']
            for etry in ctts.entries:
                sample_count += etry['sample_count']
                if sample_count >= contained_sample:
                    etry.sample_count = sample_count - contained_sample
                    break
                idx += 1
            ctts.entries = ctts.entries[:idx]

            return ctts

        
        new_moov_header = copy.deepcopy(self.parser.moov)
        video_track = None
        sound_track = None
        track_list = list(BoxUtil.find(new_moov_header, b'trak'))
        for trak in track_list:
            if BoxUtil.first(trak, b'hdlr').handler_type == b'vide':
                video_track = trak
            else:
                sound_track = trak
        
        mdat_start = 0
        mdat_end = 0
        start_timestamp = start_point
        end_timestamp = end_point

        trim_result = {
            'req_start_time': start_timestamp,
            'req_end_time': end_timestamp,
            'video_track': { 'res_start_time': 0, 'res_end_time': 0 },
            'sound_track':{ 'res_start_time': 0, 'res_end_time': 0 }
        }

        if sync:
            chunk_s, _ = self.parser.get_chunk_by_time(timestamp=start_timestamp, track='video_track', sync=True)
            chunk_e, _ = self.parser.get_chunk_by_time(timestamp=end_timestamp, track='video_track')
            start_timestamp = float(chunk_s['timestamp'])
            end_timestamp = float(chunk_e['timestamp'])
            duration = end_timestamp - start_timestamp
        
        self.edit_mvhd_duration(new_moov_header, duration)
        for track_type in ['video_track', 'sound_track']:
            if track_type == 'video_track' and video_track:
                track = video_track
            elif track_type == 'sound_track' and sound_track:
                track = sound_track
            else:
                break
            chunk_s, _ = self.parser.get_chunk_by_time(timestamp=start_timestamp, track=track_type)
            chunk_e, _ = self.parser.get_chunk_by_time(timestamp=end_timestamp, track=track_type)
            trim_result[track_type]['res_start_time'] = chunk_s['timestamp']
            trim_result[track_type]['res_end_time'] = chunk_e['timestamp']
            if not mdat_start:
                mdat_start = chunk_s['chunk_offset']
            else:
                if mdat_start > chunk_s['chunk_offset']:
                    mdat_start = chunk_s['chunk_offset']
            if not mdat_end:
                mdat_end = chunk_e['chunk_offset']
                if mdat_end < chunk_s['chunk_offset']:
                    mdat_end = chunk_s['chunk_offset']
                
            self.edit_track_duration(new_moov_header, duration, track)
            edit_stts(self, chunk_s, chunk_e, track)
            edit_stsc(self, chunk_s, chunk_e, track, track_type)
            edit_stco(self, chunk_s, chunk_e, track, track_type)
            edit_stsz(self, chunk_s, chunk_e, track, track_type)
            if track_type == 'video_track' and video_track:
                edit_stss(self, chunk_s, chunk_e, track, track_type)
                edit_ctts(self, chunk_s, chunk_e, track, track_type)

        new_moov_header = Box.parse(Box.build(new_moov_header))
        new_mmov_header_sz = new_moov_header.end

        mdat = Box.build(dict(
            type=b'mdat',
            data=download_cb(url=url, start_byte=mdat_start, end_byte=mdat_end)
        ))

        video_track = None
        track_list = list(BoxUtil.find(new_moov_header, b'trak'))
        for trak in track_list:
            stco = BoxUtil.first(trak, b'stco')
            for etry in stco.entries:
                etry.chunk_offset = ( etry.chunk_offset - mdat_start + new_mmov_header_sz + self.parser.ftyp.end + 8)
                if etry.chunk_offset <= 0:
                    assert False
            
        
        return Box.build(self.parser.ftyp), Box.build(new_moov_header), mdat, trim_result


    def trim(self, src, start_timestr, duration, sync=False):
        """
        src : mp4 header가 포함된 binary
        start_timestamp : trim의 시작지점
        duration : trim한 동영상의 running time
        sync : iframe을 고려하여 동영상을 자름
        """
        
        def edit_stts(self, chunk_s, chunk_e, track):    
            stts = BoxUtil.first(track, b'stts')
            stts_etry = stts.entries
            chunk_start_sample_idx = chunk_s['start_sample_idx']
            chunk_end_sample_idx = chunk_e['start_sample_idx']
            consumed_sample_cnt = chunk_end_sample_idx - chunk_start_sample_idx

            _range = []
            prev = None
            for s in stts_etry:
                if not _range:
                    _range.append([0, s['sample_count']-1])
                    prev = s
                else:
                    _range.append([prev['sample_count'], prev['sample_count'] + s['sample_count']])
            
            # find the chunk started _range
            idx = 0
            for r in _range:
                if r[0] <= chunk_start_sample_idx and chunk_end_sample_idx < r[1]:
                    break
                else:
                    idx += 1
            if idx != 0:
                _range = _range[idx:]
                stts = stts.entries[idx:]
            
            sc = []
            for r in _range:
                n_s = r[1] - r[0] + 1
                if consumed_sample_cnt - n_s < 0:
                    sc.append(consumed_sample_cnt)
                else:
                    sc.append(n_s)
                    consumed_sample_cnt -= n_s
            
            for etry, c in zip(stts.entries, sc):
                etry.sample_count = c

            return stts
        
        def edit_stsc(self, chunk_s, chunk_e, track, track_type):
            stsc = BoxUtil.first(track, b'stsc')
            stsc_etry = stsc.entries
            chunk_start_idx = chunk_s['chunk_idx']
            chunk_end_idx = chunk_e['chunk_idx']
            chunk_info_arr = self.parser.get_chunk_info_arr(track_type)
            _range = []
            idx = 0
            for chunk_info in chunk_info_arr:
                if idx:
                    _range[idx-1]['last_chunk'] = chunk_info['first_chunk']-1
                _range.append({
                        'first_chunk': chunk_info['first_chunk'] - 1,
                        'last_chunk': 0,
                        'samples_per_chunk': chunk_info['samples_per_chunk']
                    })
                idx += 1
            if idx:
                _range[-1]['last_chunk'] = chunk_info['first_chunk']
            
            idx2 = 0
            for r in _range:
                if chunk_end_idx < r['first_chunk']:
                    break
                idx2 += 1
            
            _range = _range[:idx2]
            idx1 = 0
            delta = chunk_start_idx
            for r in _range:
                if r['last_chunk'] - delta > 0:
                    r['first_chunk'] = r['first_chunk'] - delta
                    if r['first_chunk'] < 0:
                        r['first_chunk'] = 0
                    r['last_chunk'] -= delta
                else:
                    idx1 += 1
            _range = _range[idx1:]

            stsc.entries = stsc_etry[idx1:idx2]
            for e, r in zip(stsc.entries, _range):
                e.first_chunk = r['first_chunk']+1

            return stsc

        def edit_stco(self, chunk_s, chunk_e, track, track_type):
            stco = BoxUtil.first(track, b'stco')
            stco.entries = stco.entries[chunk_s['chunk_idx']:chunk_e['chunk_idx']]

            return stco
        
        def edit_stsz(self, chunk_s, chunk_e, track, track_type):
            stsz = BoxUtil.first(track, b'stsz')
            stsz.entry_sizes = stsz.entry_sizes[
                chunk_s['start_sample_idx']:chunk_e['start_sample_idx']
            ]
            stsz.sample_count = len(stsz.entry_sizes)
            return stsz

        def edit_stss(self, chunk_s, chunk_e, track, track_type):
            stss = BoxUtil.first(track, b'stss')            
            stss_etry = stss.entries
            idx1 = 0
            idx2 = 0
            for etry in stss_etry:
                if etry.sample_number < chunk_s['start_sample_idx']:
                    idx1 += 1
                if etry.sample_number > chunk_e['start_sample_idx']:
                    break
                idx2 += 1
            stss.entries = stss.entries[idx1:idx2]
            for etry in stss.entries:
                etry.sample_number -= chunk_s['start_sample_idx']
            

            return stss
                
        self.parser.set_binary(src)
        self.parser.parse()

        new_moov_header = copy.deepcopy(self.parser.moov)
        video_track = None
        sound_track = None
        track_list = list(BoxUtil.find(new_moov_header, b'trak'))
        for trak in track_list:
            if BoxUtil.first(trak, b'hdlr').handler_type == b'vide':
                video_track = trak
            else:
                sound_track = trak
        
        mdat_start = 0
        mdat_end = 0
        start_timestamp = self.conver_timestr_to_timestamp(start_timestr)
        end_timestamp = start_timestamp + duration

        trim_result = {
            'req_start_time': start_timestamp,
            'req_end_time': end_timestamp,
            'video_track': { 'res_start_time': 0, 'res_end_time': 0 },
            'sound_track':{ 'res_start_time': 0, 'res_end_time': 0 }
        }

        if sync:
            chunk_s, _ = self.parser.get_chunk_by_time(timestamp=start_timestamp, track='video_track', sync=True)
            chunk_e, _ = self.parser.get_chunk_by_time(timestamp=end_timestamp, track='video_track')
            start_timestamp = float(chunk_s['timestamp'])
            end_timestamp = float(chunk_e['timestamp'])
            duration = end_timestamp - start_timestamp
        
        self.edit_mvhd_duration(new_moov_header, duration)
        for track_type in ['video_track', 'sound_track']:
            if track_type == 'video_track' and video_track:
                track = video_track
            elif track_type == 'sound_track' and sound_track:
                track = sound_track
            else:
                break
            chunk_s, _ = self.parser.get_chunk_by_time(timestamp=start_timestamp, track=track_type)
            chunk_e, _ = self.parser.get_chunk_by_time(timestamp=end_timestamp, track=track_type)
            trim_result[track_type]['res_start_time'] = chunk_s['timestamp']
            trim_result[track_type]['res_end_time'] = chunk_e['timestamp']
            if not mdat_start:
                mdat_start = chunk_s['chunk_offset']
            else:
                if mdat_start > chunk_s['chunk_offset']:
                    mdat_start = chunk_s['chunk_offset']
            if not mdat_end:
                mdat_end = chunk_e['chunk_offset']
                if mdat_end < chunk_s['chunk_offset']:
                    mdat_end = chunk_s['chunk_offset']
                
            self.edit_track_duration(new_moov_header, duration, track)
            edit_stts(self, chunk_s, chunk_e, track)
            edit_stsc(self, chunk_s, chunk_e, track, track_type)
            edit_stco(self, chunk_s, chunk_e, track, track_type)
            edit_stsz(self, chunk_s, chunk_e, track, track_type)
            if track_type == 'video_track' and video_track:
                edit_stss(self, chunk_s, chunk_e, track, track_type)
                

        new_moov_header = Box.parse(Box.build(new_moov_header))
        new_mmov_header_sz = new_moov_header.end

        mdat = Box.build(dict(
                type=b'mdat',
                data=self.parser.raw[mdat_start:mdat_end]
            ))
        
        video_track = None
        track_list = list(BoxUtil.find(new_moov_header, b'trak'))
        for trak in track_list:
            stco = BoxUtil.first(trak, b'stco')
            for etry in stco.entries:
                etry.chunk_offset = ( etry.chunk_offset - mdat_start + new_mmov_header_sz + self.parser.ftyp.end + 8)
                if etry.chunk_offset <= 0:
                    assert False
        
        """
        Because of the limitation of pymp4, just copy and past original not modified headers
        """
        """
        1. pasted stsd header
        """
        # moov_header_bin = bytearray(Box.build(new_moov_header))
        # o_track_list = list(BoxUtil.find(self.parser.moov, b'trak'))
        # for trak, o_trak in zip(track_list, o_track_list):
        #     stsd = BoxUtil.first(trak, b'stsd')
        #     o_stsd = BoxUtil.first(o_trak, b'stsd')
        #     o_raw_sz = int.from_bytes(self.parser.raw[self.parser.ftyp.end + o_stsd.offset: self.parser.ftyp.end + o_stsd.offset + 4], byteorder='big')
        #     moov_header_bin[stsd.offset:stsd.offset + o_raw_sz] = self.parser.raw[self.parser.ftyp.end + o_stsd.offset: self.parser.ftyp.end + o_stsd.offset + o_raw_sz]

        """
        2. pasted 
        """

        return Box.build(self.parser.ftyp), Box.build(new_moov_header), mdat, trim_result

if __name__ == '__main__':
    _bin = b''
    with open('./video_source/full.mp4', 'rb') as f:
        _bin = f.read()
    parser = PyMp4Wrapper()
    parser.set_binary(_bin)
    parser.parse()
    tool = MpegTool()
    ftyp_raw, moov_raw, mdat, trim_result = tool.trim(_bin, '9', 6, sync=True)
    
    file_name = './video_source/trim.mp4'
    # with open('./video_source/trim.mp4', 'wb') as f:
    #     f.write(ftyp_raw)
    #     f.write(moov_raw)
    #     f.write(mdat)
    print(json.dumps(trim_result, indent=4))
    sync_delta = trim_result['video_track']['res_start_time'] - trim_result['sound_track']['res_start_time']
    #ffmpeg_sync_cmd = "ffmpeg -i {video_file} -itsoffset {ts} -i {audio_file} -map 0:v -map 1:a -acodec copy -vcodec copy {out_file}"
    ffmpeg_sync_cmd = "ffmpeg -i {video_file} -itsoffset {ts} -i {audio_file} -map 0:v -map 1:a {codec1} copy {codec2} copy {out_file}"
    codec1 = '-vcodec'
    codec2 = '-acodec'
    if sync_delta >= 0:
        codec1 = '-acodec'
        codec2 = '-vcodec'
    # use this command to add ?-seconds delay to the audio track of a video
    
    cmd = ffmpeg_sync_cmd.format(video_file=file_name, ts=sync_delta, audio_file=file_name, out_file='trim_sync2.mp4', codec1=codec1, codec2=codec2)
    child = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = child.communicate()
    print("out %s" % stdout)
    print("err %s" % stderr)