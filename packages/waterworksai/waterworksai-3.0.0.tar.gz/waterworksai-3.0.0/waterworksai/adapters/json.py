from typing import List, Mapping, Any
from ..models.timeseries import TimeSeriesPoint


def from_json(
    data: List[Mapping[str, Any]],
    time_key: str,
    value_key: str,
) -> List[TimeSeriesPoint]:
    """
    Convert a list of JSON objects into TimeSeriesPoint instances.

    Parameters
    ----------
    data : list of dict
        Input JSON records.
    time_key : str
        Key containing timestamps.
    value_key : str
        Key containing values.

    Returns
    -------
    List[TimeSeriesPoint]
    """
    if not isinstance(data, list):
        raise ValueError("Input data must be a list of objects")

    points = []
    for i, record in enumerate(data):
        if time_key not in record:
            raise ValueError(f"Missing '{time_key}' in record {i}")
        if value_key not in record:
            raise ValueError(f"Missing '{value_key}' in record {i}")

        points.append(
            TimeSeriesPoint(
                ds=record[time_key],
                y=record[value_key],
            )
        )

    return points
