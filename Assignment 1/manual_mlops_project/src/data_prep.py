import yaml
import pandas as pd
import numpy as np
import sklearn
import sklearn.model_selection
import sklearn.preprocessing
from pathlib import Path
import matplotlib.pyplot as plt


def retrieve_data(path):
    """
        Retrieve raw data and split into feature and targets
    """

    print("RETRIEVE RAW DATA")
    df = pd.read_csv(path / configs['data']['raw_path'])
    target_cols = ['Machine failure', 'TWF', 'HDF', 'PWF', 'OSF', 'RNF']
    target = df[target_cols]
    features = df.drop(target, axis=1) # type: ignore
    print("RETRIEVE RAW DATA PASS")
    return features, target

def split_data(X, y):
    """
        Split the data into training and test data
        Data is a Time Series so we do not shuffle and divide according to 70:30 ratio
    """

    print("SPLIT DATA")
    X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(
        X, y, test_size=3000, shuffle=False
    )
    print("SPLIT DATA PASS")
    return X_train, X_test, y_train, y_test

def scale_data(data):
    """
        Scale and center the data
    """

    print("SCALE DATA")
    non_numeric_feats = data[['Product ID', 'Type', 'UDI']]  # seperate non-numeric features
    numeric_feats = data.drop(non_numeric_feats, axis=1)
    scaler = sklearn.preprocessing.StandardScaler()
    numeric_scaled = scaler.fit_transform(numeric_feats)
    numeric_scaled = pd.DataFrame(data=numeric_scaled, columns=numeric_feats.columns)
    data_scaled = pd.concat([numeric_scaled, non_numeric_feats], axis=1) # combined data
    print("SCALE DATA PASS")
    return data_scaled

if __name__ == '__main__':
    print("DATA PREP")
    parent = Path(__file__).resolve().parent.parent

    # # TODO: Decide which load is better
    with open(parent / 'config.yaml', 'r') as f:
        configs = yaml.full_load(f)  # load(f, Loader=yaml.SafeLoader)

    features, target = retrieve_data(parent)
    X_train, X_test, y_train, y_test = split_data(features, target)
    X_train_scaled = scale_data(X_train)
    X_test_scaled = scale_data(X_test)

    scaled_train_data = pd.concat([X_train_scaled, y_train], axis=1)
    scaled_test_data = pd.concat([X_test_scaled, y_test], axis=1)

    scaled_train_data.to_csv((parent / configs['data']['processed_dir'] / 'v2_scaled_train.csv'), index=False)
    scaled_test_data.to_csv((parent / configs['data']['processed_dir'] / 'v2_scaled_test.csv'), index=False)
    print('DATA PREP PASS')
