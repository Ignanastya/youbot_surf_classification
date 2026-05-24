import pickle
import numpy as np
import pandas as pd

from pathlib import Path
from dct import DCT

BASE_DIR = Path(__file__).resolve().parent
dctPath = Path(f"{BASE_DIR}/data/DCT")
filename = f'dct_models.pkl'

surfs = ['linoleum', 'grass', 'rubber_carpet', 'cell_carpet']

if __name__ == '__main__':

    with open(dctPath / filename, 'rb') as file:
        models, models_std = pickle.load(file)
    
    for surf in surfs:
        # print(f'Surface: {surf}, DCT coeffs: {models[surf].coeffs}')
        print(f'Surface: {surf}, std: {models_std[surf]}')