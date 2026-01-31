import numpy as np
import pandas as pd
from tqdm import tqdm

def pair_ps_picks_fast(picks, max_tpts_diff=15.0):
    """
    Fast pairing of P and S picks at a single station using numpy searchsorted

    Input:
    picks: dataframe with columns (phase_time, phase_type, phase_score, station_id)
           phase_type must be either 'P' or 'S'
    max_tpts_diff: maximum allowed time difference between S and P picks (in seconds
    
    Output:
    pairs: dataframe with columns (station_id, p_time, s_time, p_score, s_score)
    The output pairs satisfy:
    1. s_time > p_time
    2. s_time - p_time <= max_tpts_diff
    3. No interleaved phases between the P and S picks

    Example:
    phase_time	phase_type	phase_score	station_id	
    2019-07-05 00:01:52.320	P	0.711564	CI.CCC..HH
    2019-07-05 00:01:55.970	S	0.596195	CI.CCC..HH
    2019-07-05 00:02:05.780	P	0.233257	CI.CCC..HH
    2019-07-05 00:02:09.050	S	0.269527	CI.CCC..HH
    Given the above picks, this function should be able to
    keep the pair (2019-07-05 00:01:52.320 P) + (2019-07-05 00:01:55.970 S)
    and the pair (2019-07-05 00:02:05.780 P) + (2019-07-05 00:02:09.050 S)
    reject the pair (2019-07-05 00:01:52.320 P) + (2019-07-05 00:02:09.050 S)
    """
    # Preprocessing
    picks = picks.sort_values(by='phase_time').reset_index(drop=True)
    if picks.empty: return pd.DataFrame()
    assert picks['station_id'].nunique() == 1, "Input picks must belong to a single station"
    station_id = picks['station_id'].iloc[0]
    picks["t"] = (picks["phase_time"] - picks["phase_time"].min()).dt.total_seconds()
    p_df = picks[picks["phase_type"] == "P"].reset_index(drop=True)
    s_df = picks[picks["phase_type"] == "S"].reset_index(drop=True)
    if p_df.empty or s_df.empty: return pd.DataFrame()
    # For each P, find the range of S indices that satisfy:
    # P_time < S_time <= P_time + max_diff
    p_times = p_df['t'].values
    s_times = s_df['t'].values
    # 1. Find start index in S (S must be strictly > P)
    left_idx = np.searchsorted(s_times, p_times, side='right')
    # 2. Find end index in S (S must be <= P + max_diff)
    right_idx = np.searchsorted(s_times, p_times + max_tpts_diff, side='right')
    # Calculate how many valid S picks exist for each P
    counts = right_idx - left_idx
    # If no pairs found anywhere, return empty
    if counts.sum() == 0: return pd.DataFrame()
    # 3. Construct the indices for the pairs
    # Repeat P indices based on how many S matches they have
    p_indices = np.repeat(np.arange(len(p_df)), counts)
    # Construct S indices (concatenate ranges for each P)
    # This list comprehension is extremely fast compared to DataFrame operations
    s_indices = np.concatenate([np.arange(l, r) for l, r in zip(left_idx, right_idx) if r > l])
    # 4. Build the 'pairs' DataFrame directly (only contains valid time pairs)
    if 'phase_amplitude' not in picks.columns:
        pairs = pd.DataFrame({
            "station_id": station_id,
            "p_time": p_df.iloc[p_indices]["phase_time"].values,
            "s_time": s_df.iloc[s_indices]["phase_time"].values,
            "t_p": p_times[p_indices],
            "t_s": s_times[s_indices],
            "p_score": p_df.iloc[p_indices]["phase_score"].values,
            "s_score": s_df.iloc[s_indices]["phase_score"].values
        })
    else:
        pairs = pd.DataFrame({
            "station_id": station_id,
            "p_time": p_df.iloc[p_indices]["phase_time"].values,
            "s_time": s_df.iloc[s_indices]["phase_time"].values,
            "t_p": p_times[p_indices],
            "t_s": s_times[s_indices],
            "p_score": p_df.iloc[p_indices]["phase_score"].values,
            "s_score": s_df.iloc[s_indices]["phase_score"].values,
            "p_amplitude": p_df.iloc[p_indices]["phase_amplitude"].values,
            "s_amplitude": s_df.iloc[s_indices]["phase_amplitude"].values
        })
    # Reject if (inner P exists) AND (inner S exists) AND (earliest S < latest P)
    # find the pairs that have inner P or/and S
    idx_p_start = np.searchsorted(p_times, pairs["t_p"].values, side='right')
    idx_p_end   = np.searchsorted(p_times, pairs["t_s"].values, side='left')
    has_inner_p = idx_p_end > idx_p_start
    idx_s_start = np.searchsorted(s_times, pairs["t_p"].values, side='right')
    idx_s_end   = np.searchsorted(s_times, pairs["t_s"].values, side='left')
    has_inner_s = idx_s_end > idx_s_start
    # Initialize min_inner_s and max_inner_p arrays
    min_inner_s = np.full(len(pairs), np.inf) 
    max_inner_p = np.full(len(pairs), -np.inf)
    # find the max inner P times for each pair
    valid_p = idx_p_end[has_inner_p] - 1
    valid_p = np.maximum(valid_p, 0)
    max_inner_p[has_inner_p] = p_times[valid_p]
    # find the min inner S times for each pair
    valid_s = idx_s_start[has_inner_s]
    valid_s = np.minimum(valid_s, len(s_times) - 1)
    min_inner_s[has_inner_s] = s_times[valid_s]
    # Identify interleaved pairs
    interleaved_mask = has_inner_p & has_inner_s & (min_inner_s < max_inner_p)
    if 'phase_amplitude' in picks.columns:
        pairs = pairs[~interleaved_mask][['station_id', 'p_time', 's_time', 'p_score', 's_score', 'p_amplitude', 's_amplitude']].copy()
    else:
        pairs = pairs[~interleaved_mask][['station_id', 'p_time', 's_time', 'p_score', 's_score']].copy()
    return pairs.reset_index(drop=True)

def predict_eq_origin_times(phase_picks, site_config):
    """
    Assuming that both P and S of earthquakes have been well detected by enough stations
    Input
    phase_picks: dataframe with columns (station_id, phase_time, phase_type, phase_score)
    site_config: set the allowed maximum ts-tp and the apparent vp/vs ratio at one station
    Output
    event_picks: dataframe with columns (station_id, event_time, event_score, p_time, p_score, s_time, s_score, p_amplitude, s_amplitude)
    """
    event_picks = []
    for station_id, phase_picks_ in tqdm(phase_picks.groupby('station_id')):
        # site specific parameters
        max_tpts_dif = site_config[station_id]['max_tpts_diff']
        app_vpvs_rat = site_config[station_id]['apparent_vpvs_ratio']
        # pairing P and S arrivals
        # event_picks_ = pair_ps_picks_single(phase_picks_, max_tpts_dif)
        event_picks_ = pair_ps_picks_fast(phase_picks_, max_tpts_dif)
        if len(event_picks_) == 0:
            continue
        # calculate the origin time
        dt_tstp = (event_picks_['s_time'] - event_picks_['p_time']).dt.total_seconds()
        dt_tpto = pd.to_timedelta(dt_tstp / (app_vpvs_rat - 1), unit='s')
        event_picks_['event_time'] = event_picks_['p_time'] - dt_tpto
        # save into list for output
        event_picks.append(event_picks_)
    # merge and output
    event_picks = pd.concat(event_picks, ignore_index=True)
    event_picks['event_score'] = (event_picks['p_score'] + event_picks['s_score']) / 2.0
    if 'p_amplitude' in event_picks.columns and 's_amplitude' in event_picks.columns:
        event_picks = event_picks[['station_id', 'event_time', 'event_score', 'p_time', 'p_score', 's_time', 's_score', 'p_amplitude', 's_amplitude']].copy()
    else:
        event_picks = event_picks[['station_id', 'event_time', 'event_score', 'p_time', 'p_score', 's_time', 's_score']].copy()
    # event_picks.sort_values(by=['event_time', 'station_id'], inplace=True)
    return event_picks