# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-01-24

### Changed

- The `lcurves_by_history()` function has been renamed to `lcurves()` to make the code easier to write and understand, but `lcurves_by_history()` remains as an alias for backward compatibility.
- The `history` parameter of the `lcurves()` function has been renamed to `histories`. It can now accept a list of dictionaries with several fitting histories of keras models.

### Added

- Support for correct recognition of key names in learning history of model training with the Ultralytics YOLO library.
- Support for plotting multiple histories on a single figure using `lcurves()` function.
- The default value of the `initial_epoch` parameter of the `lcurves` function has been changed from 0 to 1.
- New parameters in `lcurves()`:
  - `color_grouping_by`: Controls curve color grouping in subplots.
  - `model_names`: Customizes legend labels for each history.
  - `optimization_modes`: Sets metric optimization direction ("min"/"max")
- New `utils` module with utility functions:
  - `get_mode_by_metric_name()`: Determines metric optimization mode.
  - `get_best_epoch_value()`: Finds optimal epoch value.
  - `history_concatenate()`: Concatenates two histories into one. The function was moved from the `lcurvetools` module to the `utils` module, but it remained available for import from the main `lcurvetools` package module.

## [1.0.1] - 2025-01-23

### Changed

The default value for the `figsize` parameter of the `lcurves_by_history()` and `lcurves_by_MLP_estimator()` functions has been changed to `None`.

## [1.0.0] - 2024-01-22

Initial release.
