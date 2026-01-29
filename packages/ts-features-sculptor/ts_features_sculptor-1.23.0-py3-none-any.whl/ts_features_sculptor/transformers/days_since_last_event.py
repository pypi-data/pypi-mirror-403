from dataclasses import dataclass
from typing import Optional

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from .time_validator import TimeValidator


@dataclass
class DaysSinceLastEvent(BaseEstimator, TransformerMixin, TimeValidator):
    """
    Календарные дни с последнего события.

    Строит:
    - last_event_day (опционально): последний день, где
       event_col > 0
    - days_since_last_event: time_day - last_event_day в днях

    Предполагает, что вход уже отсортирован по time_col (используйте
    ToDateTime и SortByTime).

    Parameters
    ----------
    time_col : str, default="time"
        Колонка с datetime.
    event_col : str, default="event_flag"
        Флаг/счетчик события. Событие, если event_col > 0.
    out_days_col : str, default="days_since_last_event"
        Выходная колонка с расстоянием в календарных днях.
    out_last_day_col : str | None, default="last_event_day"
        Выходная колонка с днем последнего события (day-normalized).
        Если None, колонка не создаётся.
    fillna_value : float | None, default=None
        Значение для NaN в out_days_col. Если None, NaN остаются
        до первого события.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame(
    ...     {
    ...         "time": pd.to_datetime(
    ...             ["2025-01-01", "2025-01-02", "2025-01-03"]
    ...         ),
    ...         "has_event": [1, 0, 1],
    ...     }
    ... ).sort_values("time")
    >>> tr = DaysSinceLastEvent(
    ...     time_col="time",
    ...     event_col="has_event",
    ...     out_days_col="days_since_last_event",
    ...     out_last_day_col="last_event_day",
    ... )
    >>> result_df = tr.transform(df)
    >>> print(result_df.to_string(index=False)
    ... )
          time  has_event last_event_day  days_since_last_event
    2025-01-01          1     2025-01-01                    0.0
    2025-01-02          0     2025-01-01                    1.0
    2025-01-03          1     2025-01-03                    0.0
    """

    time_col: str = "time"
    event_col: str = "event_flag"
    out_days_col: str = "days_since_last_event"
    out_last_day_col: str | None = "last_event_day"
    fillna_value: Optional[float] = None

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self._validate_time_column(X)
        if X.empty:
            return X.copy()

        if self.event_col not in X.columns:
            raise ValueError(
                f"DaysSinceLastEvent: нет столбца {self.event_col!r}"
            )

        df = X.copy()
        time_day = df[self.time_col].dt.normalize()

        event = pd.to_numeric(df[self.event_col], errors="coerce").fillna(0.0)
        last_event_day = time_day.where(event > 0.0).ffill()

        if self.out_last_day_col is not None:
            df[self.out_last_day_col] = last_event_day

        days_since = (time_day - last_event_day).dt.days.astype(float)
        if self.fillna_value is not None:
            days_since = days_since.fillna(float(self.fillna_value))
        df[self.out_days_col] = days_since
        return df
