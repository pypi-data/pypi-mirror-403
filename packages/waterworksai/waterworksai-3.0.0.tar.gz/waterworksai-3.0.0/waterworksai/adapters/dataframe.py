from typing import List
from pandas import DataFrame
from ..models.timeseries import TimeSeriesPoint


def from_dataframe(
    df: DataFrame,
    time_col: str,
    value_col: str,
) -> List[TimeSeriesPoint]:
    """
    Convert a pandas DataFrame into a list of TimeSeriesPoint.

    Parameters
    ----------
    df : pandas.DataFrame
        Input data frame.
    time_col : str
        Column name containing timestamps.
    value_col : str
        Column name containing flow values.

    Returns
    -------
    List[TimeSeriesPoint]
    """
    if time_col not in df.columns:
        raise ValueError(f"Column '{time_col}' not found")

    if value_col not in df.columns:
        raise ValueError(f"Column '{value_col}' not found")

    return [
        TimeSeriesPoint(ds=row[time_col], y=row[value_col])
        for _, row in df.iterrows()
    ]
