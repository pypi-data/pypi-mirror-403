from dataclasses import dataclass
from typing import Any, Dict, Optional

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from .time_validator import TimeValidator


@dataclass
class TimeGridResampler(BaseEstimator, TransformerMixin, TimeValidator):
    """
    Достраивает равномерную сетку по `freq`.

    Examples
    --------
    >>> import pandas as pd
    >>> daily = pd.DataFrame({
    ...   "time": pd.to_datetime(["2025-01-01", "2025-01-03"]),
    ...   "daily_total_sum": [150.0, 30.0],
    ... }).sort_values("time")
    >>> r = TimeGridResampler(
    ...     time_col="time",
    ...     freq="D",
    ...     fill_values={"daily_total_sum": 0.0},
    ...     start="2024-01-01",
    ...     end="2025-01-04"
    ... )
    >>> result_df = r.transform(daily)
    >>> print(result_df.to_string(index=False))
          time  daily_total_sum
    2025-01-01            150.0
    2025-01-02              0.0
    2025-01-03             30.0
    2025-01-04              0.0
    """

    time_col: str = "time"
    freq: str = "D"
    start: pd.Timestamp | str | None = None
    end: pd.Timestamp | str | None = None
    fill_values: Optional[Dict[str, Any]] = None

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self._validate_time_column(X)
        df = X.copy()
        if df.empty:
            return df

        df[self.time_col] = df[self.time_col].dt.floor(self.freq)

        if df[self.time_col].duplicated().any():
            raise ValueError("TimeGridResampler: дубликаты бакетов")

        start = (
            pd.Timestamp(self.start)
            if self.start is not None
            else df[self.time_col].min()
        )
        end = (
            pd.Timestamp(self.end)
            if self.end is not None
            else df[self.time_col].max()
        )

        start_b = start.to_period(self.freq).start_time
        end_b = end.to_period(self.freq).start_time

        if end_b < start_b:
            raise ValueError("TimeGridResampler: end < start")

        grid = pd.DataFrame(
            {self.time_col: pd.date_range(start_b, end_b, freq=self.freq)}
        )
        out = grid.merge(df, on=self.time_col, how="left")

        fill_map = (
            self.fill_values
            if self.fill_values is not None
            else {c: 0 for c in out.columns if c != self.time_col}
        )
        for c, v in fill_map.items():
            if c in out.columns:
                out[c] = out[c].fillna(v)

        return out
