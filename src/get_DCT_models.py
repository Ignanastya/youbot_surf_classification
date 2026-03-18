import pickle
import numpy as np
import pandas as pd

from pathlib import Path
from dct import DCT

import plotly.graph_objects as go

colors = {'linoleum': 'slategray',
          'grass': 'green', 
          'rubber_carpet': 'saddlebrown', 
          'cell_carpet': 'darkslategray'}

BASE_DIR = Path(__file__).resolve().parent
prepared_data = Path(f"{BASE_DIR}/data/prepared")
figures = Path(f"{BASE_DIR}/data/DCT")

if __name__ == '__main__':

    df = pd.read_csv(prepared_data / 'prep_experiment1.csv')

    dct_models = {}
    dct_models_std = {}

    fig = go.Figure(
        layout=go.Layout(
            template='plotly_white',
            width=900,
            height=500,
            xaxis=dict(title='Угол движения, °'),
            yaxis=dict(title='Суммарный ток по модулю, A'),
        )
    )

    for surf, _df in df.groupby('surface'):
        fig.add_trace(
            go.Scatter(
                x=_df['angle_deg'],
                y=_df['I_total'],
                mode='lines',
                line=dict(color=colors[surf], width=2),
                name=surf,
                legendgroup=surf,
            )
        )

    x = np.arange(-180, 176, 1)
    for idx, (surf, _df) in enumerate(df.groupby('surface')):
        dct = DCT(
            data=_df['I_total'],
            cutoff_amount=2,
            range_width=355
        )
        dct_models[surf] = dct
        dct_models_std[surf] = _df['I_std'].mean()

        fig.add_trace(
            go.Scatter(
                x=x,
                y=dct.numpy_func(x, scaled=True),
                mode='lines',
                line=dict(color='red', width=3, dash='dot'),
                name='DCT',
                showlegend=True if idx == 0 else False,
                legendgroup='DCT',
            )
        )

    export_path = figures
    export_path.mkdir(parents=True, exist_ok=True)

    fig.write_image(export_path / f'I_dct.svg')
    fig.write_html(export_path / f'I_dct.html', include_plotlyjs='cdn')

    # write ml_models
    with open(export_path / f'dct_models.pkl', 'wb') as file:
        pickle.dump((dct_models, dct_models_std), file)
