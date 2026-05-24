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
filename = 'exp_models.csv' #'all_tracks.csv' #'continuous_tracks.csv'

wheels_list = ['wheel_joint_fl', 'wheel_joint_fr', 'wheel_joint_bl', 'wheel_joint_br']

def get_prepared_df(df):
    df = df.copy()
    df['M_abs_total'] = df[wheels_list].abs().sum(axis=1)
    df['I_total'] = df['M_abs_total']/K_EF
    df['angle_deg'] = np.degrees(df['target_angle']).round().astype(int)
    # moving average filter
    df['I_total_avg'] = df.groupby('angle_deg')['I_total'] \
                            .transform(lambda x: x.rolling(window=5, min_periods=1).mean())

    prep_df = df[['angle_deg', 'target_angle', 'I_total', 'I_total_avg']].copy()
    
    return prep_df


if __name__ == '__main__':
    file_path = raw_data / filename
    if not file_path.exists():
        print(f"Файл {filename} не найден")
    else:
        exp = pd.read_csv(file_path)
        surfs = ['linoleum', 'grass', 'rubber_carpet', 'cell_carpet']
        tracks = ['with_angle', 'straight', 'square', 'hourglass', 'circle', 'figure_eight']

        # exp_wth_num = add_exp_number(exp)

        global_df = pd.DataFrame()
        for surf in surfs:
            exp_by_surf = exp[exp['surface'] == surf]
            if not exp_by_surf.empty:
                for track in tracks:
                    exp_by_track = exp_by_surf[exp_by_surf['motion_type'] == track]
                    prep_df = get_prepared_df(exp_by_track)
                    prep_df.insert(loc=0, column='motion_type', value=track)
                    prep_df.insert(loc=0, column='surface', value=surf)
                    global_df = pd.concat([global_df, prep_df])
        
        global_df.to_csv(prepared_data / f"prep_{filename}", index=False)
