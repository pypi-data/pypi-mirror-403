from typing import Literal
from collections.abc import Mapping, Sequence
import warnings
from copy import deepcopy

import matplotlib.pyplot as plt

# Keywords that indicate a metric should be minimized
MINIMIZATION_KEYWORDS = frozenset(
    ["loss", "error", "hinge", "crossentropy", "false", "divergence", "poisson"]
)

OptimizationMode = Literal["min", "max"]


def _get_n_epochs(history: Mapping) -> int:
    """Return number of epochs (length of value lists) for a history dict.
    Parameters
    ----------
    history : Mapping
        A mapping of metric names to their values over epochs.

    Raises TypeError if not all values have the same length.
    """
    n_epochs = set(map(len, history.values()))
    if len(n_epochs) != 1:
        raise TypeError(
            "The values of all `history` keys should be lists of the same "
            "length, equal to the number of epochs."
        )
    return list(n_epochs)[0]


def _get_train_key_names(keys: Sequence[str]) -> list[str]:
    """Return a list of unique train key names in the keras or YOLO style."""
    train_keys: list[str] = []
    for key in keys:
        if key.startswith("val_"):  # keras style
            train_keys.append(key[4:])
        elif key.startswith("val/"):  # YOLO style
            train_keys.append("train/" + key[4:])
        else:
            train_keys.append(key)
    return list(set(train_keys))


def _get_distinct_colors(num: int) -> list[tuple[float, float, float]]:
    """Return a list of distinct colors for plotting.

    Parameters
    ----------
    num : int
        The number of distinct colors to generate.

    Returns
    -------
    list of tuple
        A list of RGB tuples representing the colors.
    """
    # https://matplotlib.org/stable/users/explain/colors/colormaps.html#qualitative
    cmap = plt.get_cmap("tab10").colors
    if num <= 10:
        return cmap[:num]
    cmap += plt.get_cmap("tab20b").colors[::4]
    if num <= 15:
        return cmap[:num]
    cmap += plt.get_cmap("tab20c").colors[1::4]
    if num <= 20:
        return cmap[:num]
    cmap += plt.get_cmap("tab20b").colors[2::4]
    if num <= 25:
        return cmap[:num]
    cmap += plt.get_cmap("tab20").colors[1::2]
    if num <= 35:
        return cmap[:num]
    cmap += plt.get_cmap("tab20b").colors[1::4]
    if num <= 40:
        return cmap[:num]
    cmap += plt.get_cmap("tab20c").colors[2::4]
    if num <= 45:
        return cmap[:num]
    cmap += plt.get_cmap("tab20b").colors[3::4]
    if num <= 50:
        return cmap[:num]
    cmap += plt.get_cmap("tab20c").colors[::4]
    if num <= 55:
        return cmap[:num]
    cmap += plt.get_cmap("tab20c").colors[3::4]
    if num <= 60:
        return cmap[:num]

    while len(cmap) < num:
        cmap += cmap
    return cmap[:num]


def get_mode_by_metric_name(name: str) -> OptimizationMode:
    """
    Get the optimization mode (min or max) for a metric based on its name.
    If the name contains "loss", "error", "hinge", "crossentropy", "false",
    "divergence" or "poisson", it is assumed to be minimized; otherwise,
    it is assumed to be maximized.

    Parameters
    ----------
    name : str
        The name of the metric.

    Returns
    -------
    str
        The mode for the metric ('min' or 'max').

    Examples
    --------
    >>> get_mode_by_metric_name("val_loss")
    'min'

    >>> get_mode_by_metric_name("val_accuracy")
    'max'

    >>> get_mode_by_metric_name("mean_absolute_percentage_error")
    'min'
    """
    if not isinstance(name, str) or not name:
        raise TypeError("name must be a non-empty string")

    return (
        "min"
        if any(kw in name.lower() for kw in MINIMIZATION_KEYWORDS)
        else "max"
    )


def get_best_epoch_value(
    metric_values: list[float],
    metric_name: str | None = None,
    mode: Literal["auto", "min", "max"] = "auto",
    verbose: bool = True,
) -> tuple[int, float]:
    """
    Get the epoch index and value of the best metric from a list of metric values.

    The best metric is determined based on the specified optimization mode:
    - "auto": Automatically determine if the metric should be minimized or maximized
      based on its name with the `lcurves.utils.get_mode_by_metric_name` function.
    - "min": The metric is minimized (lower values are better).
    - "max": The metric is maximized (higher values are better).

    Parameters
    ----------
    metric_values : list of float
        The values of the metric at each epoch.
    metric_name : str or None, default=None
        The name of the metric (used for automatic mode detection).
    mode : {"auto", "min", "max"}, default="auto"
        The optimization mode for selecting the best epoch.
    verbose : bool, default=True
        If True, warnings will be issued if the metric does not appear
        to be optimizing as expected.

    Returns
    -------
    tuple[int, float]
        A tuple containing the best epoch index and the best value.

    Examples
    --------
    >>> get_best_epoch_value([0.5, 0.4, 0.3, 0.35], 'val_loss')
    (2, 0.3)

    >>> get_best_epoch_value([0.55, 0.62, 0.6, 0.57], 'accuracy')
    (1, 0.62)

    >>> get_best_epoch_value([0.5, 0.4, 0.3, 0.35], mode='min')
    (2, 0.3)
    """
    if not isinstance(metric_values, list):
        raise TypeError("metric_values must be a list of floats")
    if not metric_values:
        raise ValueError("metric_values must be a non-empty list")
    if len(metric_values) == 1:
        return 0, metric_values[0]
    if metric_name is not None and (
        not isinstance(metric_name, str) or not metric_name
    ):
        raise TypeError("metric_name must be a non-empty string or None")
    if mode == "auto" and metric_name is None:
        raise ValueError("metric_name must be provided when mode is 'auto'")

    _mode = get_mode_by_metric_name(metric_name) if mode == "auto" else mode
    best_value = max(metric_values) if _mode == "max" else min(metric_values)
    best_epoch = metric_values.index(best_value)

    if verbose:
        is_not_optimizing = (
            best_value <= metric_values[0]
            if _mode == "max"
            else best_value >= metric_values[0]
        )
        if is_not_optimizing:
            optimization_type = "maximized" if _mode == "max" else "minimized"
            if mode == "auto":
                warnings.warn(
                    f"Metric '{metric_name}' is detected as"
                    f" {optimization_type}, but appears not to be"
                    f" {optimization_type}. Consider using mode='min' or"
                    " mode='max'.",
                    UserWarning,
                )
            else:
                warnings.warn(
                    f"Metric seems not to be {optimization_type}, but"
                    f" mode='{_mode}' was specified. Check if this is correct.",
                    UserWarning,
                )

    return best_epoch, best_value


def history_concatenate(prev_history: dict, last_history: dict) -> dict:
    """
    Concatenate two dictionaries in the format of the `history` attribute of
    the `History` object which is returned by the [fit](https://keras.io/api/models/model_training_apis/#fit-method)
    method of the model. Additionally, the dictionaries can have an `epoch` key
    with a list of indices of the passed epochs, similar to the `epoch` field
    in the file results.csv with training results of YOLO models.

    Useful for combining histories of model fitting with two or more consecutive
    runs into a single history to plot full learning curves.

    Parameters
    ----------
    prev_history : dict
        History of the previous run of model fitting. The values of all keys
        must be lists of the same length.
    last_history : dict
        History of the last run of model fitting. The values of all keys
        must be lists of the same length.

    Returns
    -------
    dict
        Dictionary with concatenated histories. If the `epoch` key is contained
        in at least one of the input dictionaries, the output dictionary will
        contain this key with the correct list of consecutive epoch indices.

    Examples
    --------
    >>> from lcurvetools import history_concatenate, lcurves

    1. Using Keras

    >>> import keras

    [Create](https://keras.io/api/models/), [compile](https://keras.io/api/models/model_training_apis/#compile-method)
    and [fit](https://keras.io/api/models/model_training_apis/#fit-method) the keras model:
    >>> model = keras.Model(...) # or keras.Sequential(...)
    >>> model.compile(...)
    >>> hist1 = model.fit(...)

    Compile as needed and fit using possibly other parameter values:
    >>> model.compile(...)
    >>> hist2 = model.fit(...)

    Concatenate the `.history` dictionaries into one:
    >>> full_history = history_concatenate(hist1.history, hist2.history)

    Use `full_history` dictionary to plot full learning curves:
    >>> lcurves(full_history);

    2. Using Ultralytics YOLO

    >>> from ultralytics import YOLO

    [Load and train](https://docs.ultralytics.com/modes/train/#usage-examples) a model:

    >>> model = YOLO("yolo11n.pt")
    >>> model.train(data="coco8.yaml", epochs=20, ...)

    Read the training results saved in the `results.csv` file after
    training a YOLO model into the first dictionary object `history_1`.
    The typical file path is `runs/detect/train/results.csv` or similar.

    >>> import pandas as pd
    >>> history_1 = pd.read_csv("runs/detect/train/results.csv").to_dict('list')

    Additionally train of the model obtained at the previous stage with
    possibly different training parameters:

    >>> model = YOLO("runs/detect/train/weights/last.pt")
    >>> model.train(data="coco8.yaml", epochs=10, ...)

    Read the training results into the second dictionary object `history_2`.

    >>> history_2 = pd.read_csv("runs/detect/train2/results.csv").to_dict('list')

    Concatenate the two history dictionaries into one and plot full learning curves:

    >>> full_history = history_concatenate(history_1, history_2)
    >>> lcurves(full_history);
    """
    if not type(prev_history) is dict:
        raise TypeError("The `prev_history` parameter should be a dictionary.")
    if not type(last_history) is dict:
        raise TypeError("The `last_history` parameter should be a dictionary.")

    if len(prev_history) < 1:
        return last_history
    if len(last_history) < 1:
        return prev_history

    prev_epochs = set(map(len, prev_history.values()))
    if len(prev_epochs) != 1:
        raise ValueError(
            "The values of all `prev_history` keys should be lists of the same"
            " length, equaled  to the number of epochs."
        )
    prev_epochs = list(prev_epochs)[0]

    last_epochs = set(map(len, last_history.values()))
    if len(last_epochs) != 1:
        raise ValueError(
            "The values of all `last_history` keys should be lists of the same"
            " length, equaled  to the number of epochs."
        )
    last_epochs = list(last_epochs)[0]

    if "epoch" not in prev_history and "epoch" in last_history:
        full_history = {"epoch": list(range(1, prev_epochs + 1))}
    else:
        full_history = {}
    full_history.update(deepcopy(prev_history))

    for key in full_history:
        if key in last_history:
            if key == "epoch":
                full_history[key] += [
                    (
                        full_history[key][-1] + epoch - last_history[key][0] + 1
                        if epoch is not None
                        else None
                    )
                    for epoch in last_history[key]
                ]
            else:
                full_history[key] += last_history[key]
        else:
            if key == "epoch":
                full_history[key] += list(
                    range(
                        full_history[key][-1] + 1,
                        full_history[key][-1] + 1 + last_epochs,
                    )
                )
            else:
                full_history[key] += [None] * last_epochs

    for key in last_history:
        if key not in full_history:
            full_history[key] = [None] * prev_epochs + last_history[key]

    return full_history
