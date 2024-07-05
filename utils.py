from auth import main as get_data
import pandas as pd


def get_df(data=None):
    values = get_data(data)
    values = [v for v in values if v and v[0]]

    df = pd.DataFrame(values[1:], columns=values[0])
    return df
