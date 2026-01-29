from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from .time_validator import TimeValidator


@dataclass
class WorkdayWindowIndexer(BaseEstimator, TransformerMixin, TimeValidator):
    """
    Индексатор окон в рабочих днях (holiday_col==0)
    с датой-якорем anchor.

    Для каждой строки возвращает границы окна по anchor_col как индексы
    дневной сетки. Поддерживает окна назад и вперед. Имеет управление
    границами через closed.

    Parameters
    ----------
    time_col : str, default="time"
        Колонка с datetime.
    anchor_col : str | None, default=None
        Колонка с датой-якорем. Если None, используется time_col.
    holiday_col : str, default="is_holiday"
        Флаг праздника (0/1 или bool).
    window_workdays : int, default=30
        Размер окна в рабочих днях.
    direction : str, default="backward"
        При "backward" окно заканчивается в anchor,
        при  "forward" окно начинается в anchor.
    closed : str, default="both"
        "both", "left", "right", "neither".
    start_idx_col : str, default="workday_start_idx"
        Имя колонки для индекса начала окна (по anchor).
    end_idx_col : str, default="workday_end_idx"
        Имя колонки для индекса конца окна (по anchor).
    is_full_window_col : str, default="is_full_window"
        Имя колонки-флага: окно содержит window_workdays рабочих дней.
    start_day_col : str | None, default=None
        Если задано, сохраняет дату начала окна.
    end_day_col : str | None, default=None
        Если задано, сохраняет дату конца окна.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame(
    ...     {
    ...         "time": pd.to_datetime(
    ...             [
    ...                 "2025-01-07",
    ...                 "2025-01-08",
    ...                 "2025-01-09",
    ...                 "2025-01-10",
    ...                 "2025-01-11",
    ...                 "2025-01-12",
    ...                 "2025-01-13",
    ...             ]
    ...         ),
    ...         "h": [1, 1, 0, 0, 0, 0, 0],
    ...     }
    ... ).sort_values("time")
    >>> tr = WorkdayWindowIndexer(
    ...     time_col="time",
    ...     holiday_col="h",
    ...     window_workdays=2,
    ...     direction="forward",
    ...     start_idx_col="s",
    ...     end_idx_col="e",
    ...     is_full_window_col="is_full",
    ...     start_day_col="sday",
    ...     end_day_col="eday",
    ... )
    >>> result_df = tr.transform(df)
    >>> print(result_df.to_string(index=False))
          time  h  s  e       sday       eday  is_full
    2025-01-07  1  0  4 2025-01-07 2025-01-11     True
    2025-01-08  1  1  4 2025-01-08 2025-01-11     True
    2025-01-09  0  2  4 2025-01-09 2025-01-11     True
    2025-01-10  0  3  5 2025-01-10 2025-01-12     True
    2025-01-11  0  4  6 2025-01-11 2025-01-13     True
    2025-01-12  0  5  6 2025-01-12 2025-01-13     True
    2025-01-13  0  6  6 2025-01-13 2025-01-13    False
    """

    time_col: str = "time"
    anchor_col: str | None = None
    holiday_col: str = "is_holiday"
    window_workdays: int = 30
    direction: str = "backward"
    closed: str = "both"
    start_idx_col: str = "workday_start_idx"
    end_idx_col: str = "workday_end_idx"
    is_full_window_col: str = "is_full_window"
    start_day_col: str | None = None
    end_day_col: str | None = None

    def fit(self, X: pd.DataFrame, y=None):
        self._validate_time_column(X)
        return self

    @staticmethod
    def _backward_start_idx(is_workday: np.ndarray, window_workdays: int):
        n = len(is_workday)
        start_idx = np.zeros(n, dtype=int)
        k = 0
        workdays = 0
        for end in range(n):
            workdays += int(is_workday[end])
            while (
                k <= end and (workdays - int(is_workday[k])) >= window_workdays
            ):
                workdays -= int(is_workday[k])
                k += 1
            start_idx[end] = max(k - 1, 0)
        return start_idx

    @staticmethod
    def _forward_end_idx(is_workday: np.ndarray, window_workdays: int):
        n = len(is_workday)
        end_idx = np.full(n, n - 1, dtype=int)
        end_ptr = 0
        workdays = 0

        for start in range(n):
            if end_ptr < start:
                end_ptr = start
                workdays = 0

            while end_ptr < n and workdays < window_workdays:
                workdays += int(is_workday[end_ptr])
                end_ptr += 1

            needed_end = max(end_ptr - 1, start)
            end_idx[start] = min(needed_end + 1, n - 1)

            if end_ptr > start:
                workdays -= int(is_workday[start])

        return end_idx

    @staticmethod
    def _apply_closed(
        start_idx: np.ndarray, end_idx: np.ndarray, closed: str
    ):
        start = start_idx.astype(int).copy()
        end = end_idx.astype(int).copy()

        if closed in {"right", "neither"}:
            start = start + 1
        if closed in {"left", "neither"}:
            end = end - 1

        return start, end

    @staticmethod
    def _map_anchor_to_index(
        time_day: pd.Series, anchor_day: pd.Series
    ) -> np.ndarray:
        time_arr = time_day.to_numpy(dtype="datetime64[ns]")
        anchor_arr = anchor_day.to_numpy(dtype="datetime64[ns]")
        idx = np.searchsorted(time_arr, anchor_arr, side="left")
        ok = (idx >= 0) & (idx < len(time_arr)) & (time_arr[idx] == anchor_arr)
        if not ok.all():
            raise ValueError(
                "WorkdayWindowIndexer: anchor values must be in time grid"
            )
        return idx

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self._validate_time_column(X)
        if X.empty:
            return X.copy()

        missing = [
            c for c in [self.holiday_col] if c not in X.columns
        ]
        if missing:
            raise ValueError(
                f"WorkdayWindowIndexer: missing columns: {missing}"
            )

        if self.anchor_col is not None and self.anchor_col not in X.columns:
            raise ValueError(
                f"WorkdayWindowIndexer: missing anchor {self.anchor_col!r}"
            )

        if self.direction not in {"backward", "forward"}:
            raise ValueError("WorkdayWindowIndexer: invalid direction")
        if self.closed not in {"both", "left", "right", "neither"}:
            raise ValueError("WorkdayWindowIndexer: invalid closed")
        if self.window_workdays <= 0:
            raise ValueError("WorkdayWindowIndexer: window_workdays <= 0")

        df = X.copy()
        time_day = df[self.time_col].dt.normalize()
        if time_day.duplicated().any():
            raise ValueError("WorkdayWindowIndexer: duplicated time_day")

        anchor_day = (
            df[self.anchor_col].dt.normalize()
            if self.anchor_col is not None
            else time_day
        )

        is_holiday = pd.to_numeric(
            df[self.holiday_col], errors="coerce"
        ).fillna(0.0)
        is_workday = (is_holiday.to_numpy(dtype=float) == 0.0).astype(int)

        n = len(df)
        if self.direction == "backward":
            start_idx = self._backward_start_idx(
                is_workday, self.window_workdays
            )
            end_idx = np.arange(n, dtype=int)
        else:
            start_idx = np.arange(n, dtype=int)
            end_idx = self._forward_end_idx(is_workday, self.window_workdays)

        start_adj, end_adj = self._apply_closed(
            start_idx, end_idx, self.closed
        )
        anchor_idx = self._map_anchor_to_index(time_day, anchor_day)

        start_for_row = start_adj[anchor_idx]
        end_for_row = end_adj[anchor_idx]

        df[self.start_idx_col] = start_for_row
        df[self.end_idx_col] = end_for_row

        empty = start_for_row > end_for_row
        if self.start_day_col is not None:
            start_day = time_day.to_numpy()
            start_map = start_day[np.clip(start_for_row, 0, n - 1)]
            start_map = np.where(empty, np.datetime64("NaT"), start_map)
            df[self.start_day_col] = start_map

        if self.end_day_col is not None:
            end_day = time_day.to_numpy()
            end_map = end_day[np.clip(end_for_row, 0, n - 1)]
            end_map = np.where(empty, np.datetime64("NaT"), end_map)
            df[self.end_day_col] = end_map

        prefix = np.cumsum(is_workday, dtype=int)
        workdays_cnt = np.zeros(n, dtype=int)
        ok = ~empty
        if ok.any():
            s = np.clip(start_for_row[ok], 0, n - 1)
            e = np.clip(end_for_row[ok], 0, n - 1)

            sum_ = prefix[e]
            has_prev = s > 0
            if has_prev.any():
                sum_[has_prev] = sum_[has_prev] - prefix[s[has_prev] - 1]
            workdays_cnt[ok] = sum_
        df[self.is_full_window_col] = (workdays_cnt >= self.window_workdays)
        return df
