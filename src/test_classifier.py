import pickle
from copy import copy
from functools import partial
from multiprocessing import Pool
from pathlib import Path

import joblib
import pandas as pd
from surface_classifier import Classifier, MedianModel, MetricNormal
from time import time

BASE_DIR = Path(__file__).resolve().parent
prepared_data = Path(f"{BASE_DIR}/data/prepared")
classifPath = Path(f"{BASE_DIR}/data/classifier")


def task(df, cols, classifier, feature):
    df[cols] = df.apply(
        lambda x: classifier.classify_type_and_prob(x['angle_deg'], x[feature]), axis=1, result_type='expand')
    return df


if __name__ == '__main__':
    feature = 'I_total'

    df = pd.read_csv(prepared_data / 'prep_rub_tracks_old.csv')

    surfs = ['linoleum', 'grass', 'rubber_carpet', 'cell_carpet']
    num_of_coeffs = {s: 4 for s in surfs}

    # load classsifier
    classifier = joblib.load(f'{classifPath}/surface_classifier.joblib')

    # test classifier
    cols = []
    for cls_type in ('raw', 'memory'):
        cols += [f'cls_{cls_type}'] + [f'{s}_{cls_type}' for s in surfs]

    args = ((_df, cols, copy(classifier), feature) for (surface, angle_deg), _df in
            df.groupby(['surface', 'angle_deg']))


    print(f'Starting test for alpha: {classifier.alpha}')
    start_time = time()
    with Pool(processes=6) as p:
        res = p.starmap(task, args)
    end_time = time()
    print(f'Time taken: {end_time - start_time:.4f} s.')
    print('Exporting results to file')

    export_path = classifPath
    export_path.mkdir(parents=True, exist_ok=True)
    pd.concat(res, axis=0).to_csv(export_path / 'cls_results_3_05.csv', index=False)