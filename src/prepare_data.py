import pandas as pd
import numpy as np
import math
from pathlib import Path

# Torque coefficient
K_M = 0.0335
G = 26  # gear ratio
K_EF = K_M * G

BASE_DIR = Path(__file__).resolve().parent
raw_data = Path(f"{BASE_DIR}/data/raw")
prepared_data = Path(f"{BASE_DIR}/data/prepared")
filename = 'cell_tracks.csv'

wheels_list = ['wheel_joint_fl', 'wheel_joint_fr', 'wheel_joint_bl', 'wheel_joint_br']

def calc_current(df, title):
    for wheel in wheels_list:
        df[f'{title}_{wheel}'] = df[wheel]/K_EF
    df.drop(wheels_list, axis=1, inplace=True)

def add_exp_number(df):
    numbered_df = df.copy()
    new_exp_trigger = numbered_df['time'] < numbered_df['time'].shift()
    numbered_df['number'] = new_exp_trigger.astype(int).cumsum()
    # numbered_df.insert(loc=0, column='number', value=new_exp_trigger.astype(int).cumsum())
    return numbered_df

def get_prepared_df(df, moving_avrg=False):
    # prep_df_mean = df.groupby('target_angle')[wheels_list].mean().reset_index()
    # calc_current(prep_df_mean, 'I_mean')

    # prep_df_std = df.groupby('target_angle')[wheels_list].std().reset_index()
    # calc_current(prep_df_std, 'I_std')

    # prep_df = pd.merge(prep_df_mean, prep_df_std, on='target_angle')
    # prep_df.insert(loc=0, column='angle_deg', value=round(np.degrees(prep_df['target_angle'])))

    # cols = [f'I_mean_{wheel}' for wheel in wheels_list]
    # prep_df['I_total'] = prep_df[cols].abs().sum(axis=1)
    # prep_df['I_std'] = prep_df[cols].std(axis=1)
    
    # return prep_df

    df = df.copy()

    if (moving_avrg): 
        window_size = 5
        for wheel in wheels_list:
            df[wheel] = df[wheel].rolling(window=window_size, min_periods=1).mean()

    prep_df_mean = df.groupby(['number', 'target_angle'])[wheels_list].mean().reset_index()
    calc_current(prep_df_mean, 'I_mean')

    prep_df_std = df.groupby(['number', 'target_angle'])[wheels_list].std().reset_index()
    calc_current(prep_df_std, 'I_std')

    prep_df = pd.merge(prep_df_mean, prep_df_std, on=['number', 'target_angle'])
    prep_df.insert(loc=0, column='angle_deg', value=round(np.degrees(prep_df['target_angle'])))

    cols = [f'I_mean_{wheel}' for wheel in wheels_list]
    prep_df['I_total'] = prep_df[cols].abs().sum(axis=1)
    prep_df['I_std'] = prep_df[cols].std(axis=1)
    
    return prep_df


if __name__ == '__main__':
    exp = pd.read_csv(raw_data / filename)
    surfs = ['linoleum', 'grass', 'rubber_carpet', 'cell_carpet']
    tracks = ['with_angle', 'straight', 'square', 'hourglass']

    exp_wth_num = add_exp_number(exp)

    global_df = pd.DataFrame()
    for surf in surfs:
        exp_by_surf = exp_wth_num[exp_wth_num['surface'] == surf]
        if not exp_by_surf.empty:
            for track in tracks:
                exp_by_track = exp_by_surf[exp_by_surf['motion_type'] == track]
                prep_df = get_prepared_df(exp_by_track)
                prep_df.insert(loc=0, column='motion_type', value=track)
                prep_df.insert(loc=0, column='surface', value=surf)
                global_df = pd.concat([global_df, prep_df])
    
    global_df.to_csv(prepared_data / f"prep_{filename}", index=False)
