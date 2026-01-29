import numpy as np
import pandas as pd
from dataclasses import dataclass
from sklearn.base import BaseEstimator, TransformerMixin

from .time_validator import TimeValidator


@dataclass
class IndexedWindowAggregator(BaseEstimator, TransformerMixin, TimeValidator):
    """
    Агрегатор по заранее рассчитанным границам окон.

    Использует индексы начала/конца окна в строках датафрейма, например,
    полученные WorkdayWindowIndexer.

    Parameters
    ----------
    time_col : str, default="time"
        Колонка с datetime (для проверки сортировки).
    value_col : str, default="value"
        Колонка с числовыми значениями.
    start_idx_col : str, default="workday_start_idx"
        Имя колонки с индексом начала окна.
    end_idx_col : str, default="workday_end_idx"
        Имя колонки с индексом конца окна.
    agg : str, default="sum"
        "sum", "count" или "mean".
    fillna_value : float | None, default=0.0
        Если не None, заменяет NaN в результате.
    out_col : str, default="window_value"
        Имя выходной колонки.

    Notes
    -----
    Всегда аггрегирует по интервалу с включенными границами
    [start_idx, end_idx].

    Семантики left, right, both, neither должны быть учтены при
    построении индексов, как, например, в WorkdayWindowIndexer.

    Examples
    --------
    >>> import pandas as pd
    >>> base_df = pd.DataFrame(
    ...     {
    ...         "time": pd.to_datetime(
    ...             ["2025-01-01", "2025-01-02", "2025-01-03"]
    ...         ),
    ...         "value": [1.0, 2.0, 3.0],
    ...         "start_idx": [0, 0, 0],
    ...         "end_idx": [0, 1, 2],
    ...     }
    ... ).sort_values("time")
    >>> agg = IndexedWindowAggregator(
    ...     time_col="time",
    ...     value_col="value",
    ...     start_idx_col="start_idx",
    ...     end_idx_col="end_idx",
    ...     agg="sum",
    ...     out_col="value_w2",
    ... )
    >>> result_df = agg.transform(base_df)
    >>> print(result_df.to_string(index=False))
          time  value  start_idx  end_idx  value_w2
    2025-01-01    1.0          0        0       1.0
    2025-01-02    2.0          0        1       3.0
    2025-01-03    3.0          0        2       6.0
    """

    time_col: str = "time"
    value_col: str = "value"
    start_idx_col: str = "workday_start_idx"
    end_idx_col: str = "workday_end_idx"
    agg: str = "sum"
    fillna_value: float | None = 0.0
    out_col: str = "window_value"

    def fit(self, X: pd.DataFrame, y=None):
        self._validate_time_column(X)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self._validate_time_column(X)
        if X.empty:
            return X.copy()

        needed = [self.value_col, self.start_idx_col, self.end_idx_col]
        missing = [c for c in needed if c not in X.columns]
        if missing:
            raise ValueError(
                f"IndexedWindowAggregator: missing columns: {missing}"
            )

        if self.agg not in {"sum", "count", "mean"}:
            raise ValueError("IndexedWindowAggregator: invalid agg")

        df = X.copy()
        values = pd.to_numeric(
            df[self.value_col], errors="coerce"
        ).astype(float)
        if self.fillna_value is not None:
            values = values.fillna(float(self.fillna_value))
        values_arr = values.to_numpy(dtype=float)

        start_arr = pd.to_numeric(
            df[self.start_idx_col], errors="coerce"
        ).to_numpy(dtype=float)
        end_arr = pd.to_numeric(
            df[self.end_idx_col], errors="coerce"
        ).to_numpy(dtype=float)

        start_arr = np.nan_to_num(start_arr, nan=-1.0).astype(int)
        end_arr = np.nan_to_num(end_arr, nan=-2.0).astype(int)

        n = len(df)
        start = np.clip(start_arr, 0, n - 1)
        end = np.clip(end_arr, -1, n - 1)

        empty = start > end
        prefix = np.cumsum(values_arr, dtype=float)

        out = np.full(n, np.nan, dtype=float)
        ok = ~empty
        if ok.any():
            s = start[ok]
            e = end[ok]

            sum_ = prefix[e]
            has_prev = s > 0
            if has_prev.any():
                sum_[has_prev] = sum_[has_prev] - prefix[s[has_prev] - 1]

            if self.agg == "sum":
                out[ok] = sum_
            elif self.agg == "count":
                out[ok] = (e - s + 1).astype(float)
            else:
                cnt = (e - s + 1).astype(float)
                out[ok] = np.where(cnt > 0.0, sum_ / cnt, np.nan)

        df[self.out_col] = out
        if self.fillna_value is not None:
            df[self.out_col] = df[self.out_col].fillna(
                float(self.fillna_value)
            )
        return df
