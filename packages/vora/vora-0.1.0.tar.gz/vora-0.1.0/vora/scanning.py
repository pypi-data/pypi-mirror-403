import obspy
import fsspec
import pandas as pd
from tqdm import tqdm
from obspy import Inventory
from matplotlib.dates import num2date
from obspy.imaging.scripts.scan import Scanner

"""
three types of data availability at different stations
1. picks data
2. station inventory
3. waveform data
IMPORTANT:
Smaller delta will reflect more transient change of the availability
This controls the smallest time window for which graph to be generated
"""

def has_overlap(time_window1, time_window2):
    return max(time_window1[0], time_window2[0]) < min(time_window1[1], time_window2[1])

def scan_station_availability_using_picks(picks, tmin=None, tmax=None, delta=pd.Timedelta(1, 'D'), station_id_key='station_id'):
    picks['phase_time'] = pd.to_datetime(picks['phase_time'])
    if tmin is None: tmin = picks['phase_time'].min().floor(delta)
    if tmax is None: tmax = picks['phase_time'].max().ceil(delta) - delta
    intervals = []
    for start_time in pd.date_range(tmin, tmax, freq=delta):
        end_time = start_time + delta
        picks_ = picks[(picks['phase_time'] >= start_time) & (picks['phase_time'] < end_time)].copy()
        if picks_.empty:
            continue
        station_ids = ",".join(sorted(picks_[station_id_key].unique()))
        intervals.append({
            'start_time': start_time,
            'end_time': end_time,
            'station_ids': station_ids
        })
    intervals = pd.DataFrame(intervals)
    intervals = intervals.sort_values('start_time').reset_index(drop=True)
    intervals['station_ids_changed'] = (intervals['station_ids'] != intervals['station_ids'].shift())
    intervals['group'] = intervals['station_ids_changed'].cumsum()
    intervals = (intervals.groupby('group', as_index=False)
        .agg(
            start_time=('start_time', 'first'),
            end_time=('end_time', 'last'),
            station_ids=('station_ids', 'first')
        ))
    intervals.drop(columns=['group'], inplace=True)
    intervals.reset_index(drop=True, inplace=True)
    availability = {}
    for idx, row in intervals.iterrows():
        start_time = row['start_time']
        end_time = row['end_time']
        station_ids = row['station_ids']
        key = f"{start_time.strftime('%Y-%m-%dT%H:%M:%S')}_{end_time.strftime('%Y-%m-%dT%H:%M:%S')}"
        availability[key] = {'start_time': start_time, 'end_time': end_time, 'station_ids': station_ids}
    return availability

def scan_station_availability_using_inventory(inventory, tmin, tmax, delta=pd.Timedelta(1, 'D')):
    # 
    def parse_inventory(inv: Inventory) -> pd.DataFrame:
        df = []
        for net in inv:
            for sta in net:
                for cha in sta:
                    df.append(
                        {
                            "station_id": f"{net.code}.{sta.code}.{cha.location_code}.{cha.code[:-1]}",
                            "begin_time": (
                                cha.start_date.datetime.isoformat()
                                if cha.start_date is not None
                                else "1970-01-01T00:00:00"
                            ),
                            "end_time": (
                                cha.end_date.datetime.isoformat()
                                if cha.end_date is not None
                                else "3000-01-01T00:00:00"
                            ),})
        df = pd.DataFrame(df)
        return df
    df = parse_inventory(inventory)
    tmin, tmax = pd.to_datetime(tmin), pd.to_datetime(tmax)
    intervals = []
    for start_time in pd.date_range(tmin.floor(delta), tmax.ceil(delta) - delta, freq=delta):
        end_time = start_time + delta
        df['overlap'] = df.apply(lambda row: has_overlap([start_time.isoformat(), end_time.isoformat()], [row['begin_time'], row['end_time']]), axis=1)
        station_ids = ",".join(sorted(df[df['overlap']]['station_id'].unique()))
        intervals.append({
            'start_time': start_time,
            'end_time': end_time,
            'station_ids': station_ids
        })
    intervals = pd.DataFrame(intervals)
    intervals = intervals.sort_values('start_time').reset_index(drop=True)
    intervals['station_ids_changed'] = (intervals['station_ids'] != intervals['station_ids'].shift())
    intervals['group'] = intervals['station_ids_changed'].cumsum()
    intervals = (intervals.groupby('group', as_index=False)
        .agg(
            start_time=('start_time', 'first'),
            end_time=('end_time', 'last'),
            station_ids=('station_ids', 'first')
        ))
    intervals.drop(columns=['group'], inplace=True)
    intervals.reset_index(drop=True, inplace=True)
    availability = {}
    for idx, row in intervals.iterrows():
        start_time = row['start_time']
        end_time = row['end_time']
        station_ids = row['station_ids'].split(",")
        key = f"{start_time.strftime('%Y-%m-%dT%H:%M:%S')}_{end_time.strftime('%Y-%m-%dT%H:%M:%S')}"
        availability[key] = {'start_time': start_time, 'end_time': end_time, 'station_ids': station_ids}
    return availability

def scan_station_availability_using_waveforms(file_list, tmin, tmax, delta=pd.Timedelta(1, 'D')):
    def read_seis_file(path):
        try:
            with fsspec.open(path, "rb", anon=True) as fs:
                st = obspy.read(fs, headonly=True)
                return st
        except Exception as e:
            print(e)
            return None

    scanner = Scanner()
    for file in tqdm(file_list, desc="scanning waveform data ... (may take a while)"):
        st = read_seis_file(file)
        if st is None: continue
        scanner.add_stream(st)
    scanner.analyze_parsed_data()

    df = []
    for seed_id in sorted(list(scanner._info.keys())):
        network, station, location, channel = seed_id.split('.')
        station_id = f"{network}.{station}.{location}.{channel[:-1]}"
        data_startends_compressed = scanner._info[seed_id]['data_startends_compressed']
        for start_num, end_num in data_startends_compressed:
            df.append(
                {
                "station_id": station_id,
                "start_time": num2date(start_num).replace(tzinfo=None).isoformat(),
                "end_time": num2date(end_num).replace(tzinfo=None).isoformat()
                }
            )
    df = pd.DataFrame(df)
    intervals = []
    for start_time in pd.date_range(tmin.floor(delta), tmax.ceil(delta) - delta, freq=delta):
        end_time = start_time + delta
        df['overlap'] = df.apply(lambda row: has_overlap([start_time.isoformat(), end_time.isoformat()], [row['start_time'], row['end_time']]), axis=1)
        station_ids = ",".join(sorted(df[df['overlap']]['station_id'].unique()))
        intervals.append({
            'start_time': start_time,
            'end_time': end_time,
            'station_ids': station_ids
        })
    intervals = pd.DataFrame(intervals)
    intervals = intervals.sort_values('start_time').reset_index(drop=True)
    intervals['station_ids_changed'] = (intervals['station_ids'] != intervals['station_ids'].shift())
    intervals['group'] = intervals['station_ids_changed'].cumsum()
    intervals = (intervals.groupby('group', as_index=False)
        .agg(
            start_time=('start_time', 'first'),
            end_time=('end_time', 'last'),
            station_ids=('station_ids', 'first')
        ))
    intervals.drop(columns=['group'], inplace=True)
    intervals.reset_index(drop=True, inplace=True)
    availability = {}
    for idx, row in intervals.iterrows():
        start_time = row['start_time']
        end_time = row['end_time']
        station_ids = row['station_ids'].split(",")
        key = f"{start_time.strftime('%Y-%m-%dT%H:%M:%S')}_{end_time.strftime('%Y-%m-%dT%H:%M:%S')}"
        availability[key] = {'start_time': start_time, 'end_time': end_time, 'station_ids': station_ids}
    return availability