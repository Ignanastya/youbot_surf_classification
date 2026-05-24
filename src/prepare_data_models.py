import pandas as pd
import numpy as np
from pathlib import Path

# Torque coefficient
K_M = 0.0335
G = 26  # gear ratio
K_EF = K_M * G

BASE_DIR = Path(__file__).resolve().parent
raw_data = Path(f"{BASE_DIR}/data/raw")
prepared_data = Path(f"{BASE_DIR}/data/prepared")
filename = 'exp_models.csv'

wheels_list = ['wheel_joint_fl', 'wheel_joint_fr', 'wheel_joint_bl', 'wheel_joint_br']


def get_prepared_df(df):
    df = df.copy()
    df['M_abs_total'] = df[wheels_list].abs().sum(axis=1)
    df['I_total'] = df['M_abs_total']/K_EF
    df['angle_deg'] = np.degrees(df['target_angle']).round().astype(int)

    prep_df = df.groupby(['angle_deg', 'target_angle']).agg(
        I_total_mean=('I_total', 'mean'),
        I_total_std=('I_total', 'std'),
    ).reset_index()
    
    return prep_df


if __name__ == '__main__':
    file_path = raw_data / filename
    if not file_path.exists():
        print(f"Файл {filename} не найден")
    else:
        exp = pd.read_csv(file_path)
        surfs = ['linoleum', 'grass', 'rubber_carpet', 'cell_carpet']

        global_df = pd.DataFrame()
        for surf in surfs:
            exp_by_surf = exp[exp['surface'] == surf]
            if not exp_by_surf.empty:
                prep_df = get_prepared_df(exp_by_surf)
                prep_df.insert(loc=0, column='surface', value=surf)
                global_df = pd.concat([global_df, prep_df])

        prepared_data.mkdir(parents=True, exist_ok=True)
        output_file = prepared_data / f"prepModels_{filename}"
        global_df.to_csv(output_file, index=False)
        print(f"Успешно сохранено: {output_file}")
