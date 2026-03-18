import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
prepared_data = Path(f"{BASE_DIR}/data/prepared")
plots_img = Path(f"{BASE_DIR}/data/plots")
filename = 'prep_experiment1.csv'

wheels_list = ['wheel_joint_fl', 'wheel_joint_fr', 
               'wheel_joint_bl', 'wheel_joint_br']
labels = ['Колесо переднее левое', 'Колесо переднее правое', 
          'Колесо заднее левое', 'Колесо заднее правое']

def meanCurrentByAng(df, ymin, ymax):
    plt.figure(figsize=(10, 5))
    for wheel, label in zip(wheels_list, labels):
        plt.plot(df['angle_deg'], df[f'I_mean_{wheel}'], marker='o', label=label)

        plt.fill_between(df['angle_deg'],
                     df[f'I_mean_{wheel}'] - df[f'I_std_{wheel}'], 
                     df[f'I_mean_{wheel}'] + df[f'I_std_{wheel}'], 
                     alpha=0.3)
    
    plt.xticks(np.arange(-180, 200, step=20))
    plt.ylim(ymin, ymax)
    plt.xlabel('Угол движения, °')
    plt.ylabel('Средний ток, A')
    plt.grid(True)
    plt.legend(loc='lower right', bbox_to_anchor=(1, 1))
    # plt.show()
    plt.savefig(plots_img / f'{surf}.png', bbox_inches='tight')
    plt.close()


def currentSumByAng(df, label, color):
    plt.plot(df['angle_deg'], df['I_total'], marker='o', label=label, color=color)
    plt.fill_between(df['angle_deg'],
                     df['I_total'] - df['I_std'], 
                     df['I_total'] + df['I_std'], 
                     alpha=0.3, label=label+' ±σ', color=color)


if __name__ == '__main__':
    plots_img.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(prepared_data / filename)
    surfs = ['linoleum', 'grass', 'rubber_carpet', 'cell_carpet']
    limits = [(-1.75, 2), (-4.5, 4.5), (-5, 5), (-3, 3)]

    # Графики среднего тока всех колес
    for surf, lim in zip(surfs, limits):
        df_by_surf = df[df['surface'] == surf]
        meanCurrentByAng(df_by_surf, lim[0], lim[1])

    colors = ['slategray', 'green', 'saddlebrown', 'darkslategray']

    # Графики суммарного тока колес по модулю
    plt.figure(figsize=(10, 6))
    for surf, color in zip(surfs, colors):
        df_by_surf = df[df['surface'] == surf]
        currentSumByAng(df_by_surf, surf, color)
    
    plt.xticks(np.arange(-180, 200, step=20))
    plt.ylim(0, 16)
    plt.xlabel('Угол движения, °')
    plt.ylabel('Суммарный ток по модулю, A')
    plt.grid(True)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    # plt.show()
    plt.savefig(plots_img / 'summary.png', bbox_inches='tight')
    plt.close()

    