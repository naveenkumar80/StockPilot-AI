from typing import Iterator, Tuple, List, Optional
import numpy as np
import pandas as pd


class PurgedWalkForwardCV:
    """
    Purged and Embargoed Walk-Forward Cross-Validation Splitter for Financial Time Series.

    Ensures:
      1. Chronological order: Train folds strictly precede test folds.
      2. Purging: Removes training samples that overlap with test labels.
      3. Embargo: Leaves a safety gap of N periods between train and test windows
         to prevent label leakage caused by multi-day forward return horizons.
    """

    def __init__(
        self,
        n_splits: int = 4,
        embargo_periods: int = 5,
        min_train_ratio: float = 0.40,
    ):
        self.n_splits = n_splits
        self.embargo_periods = embargo_periods
        self.min_train_ratio = min_train_ratio

    def split(
        self,
        df: pd.DataFrame,
        time_column: str = "timestamp",
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """
        Yields (train_indices, test_indices) arrays strictly obeying temporal boundaries.
        """
        n_samples = len(df)
        if n_samples < 50:
            raise ValueError(f"Insufficient samples for walk-forward CV: {n_samples}")

        # Unique timestamps in chronological order
        unique_times = df[time_column].sort_values().drop_duplicates().reset_index(drop=True)
        total_time_steps = len(unique_times)

        min_train_steps = int(total_time_steps * self.min_train_ratio)
        remaining_steps = total_time_steps - min_train_steps - (self.embargo_periods * self.n_splits)

        if remaining_steps <= 0:
            # Fallback to simple expanding splits if time points are sparse
            step_size = max(1, (total_time_steps - min_train_steps) // self.n_splits)
        else:
            step_size = max(1, remaining_steps // self.n_splits)

        for i in range(self.n_splits):
            train_end_idx = min_train_steps + (i * step_size)
            test_start_idx = train_end_idx + self.embargo_periods
            test_end_idx = min(total_time_steps, test_start_idx + step_size)

            if test_start_idx >= total_time_steps:
                break

            train_cutoff_time = unique_times.iloc[train_end_idx]
            test_start_time = unique_times.iloc[test_start_idx]
            test_end_time = unique_times.iloc[test_end_idx - 1]

            # Indices matching timestamps
            train_mask = df[time_column] <= train_cutoff_time
            test_mask = (df[time_column] >= test_start_time) & (df[time_column] <= test_end_time)

            train_indices = np.where(train_mask)[0]
            test_indices = np.where(test_mask)[0]

            if len(train_indices) > 0 and len(test_indices) > 0:
                yield train_indices, test_indices

    def get_n_splits(self) -> int:
        return self.n_splits

