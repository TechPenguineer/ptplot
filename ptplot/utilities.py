import dask.dataframe as dd
import functools
import numpy as np
import pandas as pd
import warnings

from typing import Any, Callable, Sequence, Union


class DaskCompatibilityWarning(UserWarning):  # pragma: no cover
    """
    A warning for cases where some noncritical functionality
    is skipped because it does not work in dask. For example,
    skipping error checking that works for pandas but would
    require running ``.compute()`` for dask, instead this will
    raise a warning explaining that the user needs to be
    responsible for that checking themselves.
    """

    pass


def warn_if_dask(input_dataframe):  # pragma: no cover
    if type(input_dataframe) == dd.DataFrame:
        warnings.warn(
            "Error checking suppressed with dask dataframes to prevent " "unnecessary compute calls",
            DaskCompatibilityWarning,
        )


def get_path_midpoint(path):  # pragma: no cover
    min_x, max_x, min_y, max_y = path.bbox()
    midpoint_x = (max_x + min_x) / 2
    midpoint_y = (max_y + min_y) / 2
    return complex(midpoint_x, midpoint_y)


def make_vline(y0, y1, x, **kwargs):  # pragma: no cover
    """Make a vertical line of a defined distance."""
    return dict(type="line", y0=y0, y1=y1, x0=x, x1=x, **kwargs)


def make_hline(x0, x1, y, **kwargs):  # pragma: no cover
    """Make a horizontal line of a defined distance."""
    return dict(type="line", y0=y, y1=y, x0=x0, x1=x1, **kwargs)


def generate_time_elapsed_labels(time_zeropoint, time_column_name, formatting="{:.2f} s"):
    """Create a function that can be used in plotting animations to show time elapsed compared
    to a user-defined zeropoint.
    """

    def time_elapsed_function(frame_data):
        frame_times = frame_data[time_column_name]
        max_frame_time = frame_times.max()
        min_frame_time = frame_times.min()
        if max_frame_time != min_frame_time:
            raise ValueError(f"Frame has multiple times: {min_frame_time}, {max_frame_time}")
        time_elapsed = (max_frame_time - time_zeropoint) / np.timedelta64(1, "s")
        return formatting.format(time_elapsed)

    return time_elapsed_function


def generate_labels_from_columns(
    columns: Sequence[str],
    column_formatting: Union[Sequence[str], None] = None,
    separator: str = " ",
    na_rep: Union[str, None] = None,
):
    """Concatenate columns of a dataframe together to create formatted text labels."""
    if column_formatting is not None and len(columns) != len(column_formatting):
        raise IndexError("If column_formatting is used, must have the same length as columns")
    if column_formatting is None:
        column_formatting = [None] * len(columns)

    def column_concat_function(data):
        string_columns = [
            data[column].astype(str) if formatter is None else data[column].map(formatter.format)
            for column, formatter in zip(columns, column_formatting)
        ]
        labels = functools.reduce(lambda x, y: x.str.cat(y, sep=separator, na_rep=na_rep), string_columns)
        return labels

    return column_concat_function


def _parse_none_callable_string(
    object_to_parse: Union[None, Callable, str],
    data: pd.DataFrame,
    default_value: Any
):
    """Takes an argument that may be one of None, a column in a dataframe, or a function which operates
    on the dataframe.
    """
    if object_to_parse is None:
        # Set the default
        return np.tile([default_value], len(data))
    try:
        # Is it a function? If so, call it using data as the argument
        parsed_data = object_to_parse(data)
    except TypeError:
        # If not a function, then it should be a string. `.values` ensures a numpy array is returned
        return data[object_to_parse].values
    # If it was a function, let's make sure it's not a pandas Series (to avoid potential issues with
    # indexing
    try:
        return parsed_data.values
    except AttributeError:
        return parsed_data
