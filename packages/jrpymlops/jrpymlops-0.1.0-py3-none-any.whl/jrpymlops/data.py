import pandas as pd
import pkg_resources


def load(file):
    # Ensure file has .zip extension
    file += '.zip' * (not file.endswith('.zip'))

    # Path to data relative to package
    data_path = f'data/{file}'

    # Absolute path to data
    abs_path = pkg_resources.resource_filename(__name__, data_path)

    return pd.read_csv(abs_path)
