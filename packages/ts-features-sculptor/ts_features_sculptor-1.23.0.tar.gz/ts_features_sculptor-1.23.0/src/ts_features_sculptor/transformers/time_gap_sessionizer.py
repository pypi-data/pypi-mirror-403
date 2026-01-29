import pandas as pd
from dataclasses import dataclass
from sklearn.base import BaseEstimator, TransformerMixin

from .time_validator import TimeValidator


@dataclass
class TimeGapSessionizer(BaseEstimator, TransformerMixin, TimeValidator):
    """
    Трансформер для схлопывания последовательности событий в сессии
    по пороговому временному разрыву.

    Время сессии задаётся как время первого события в сессии.

    Parameters
    ----------
    time_col : str, default="time"
        Название столбца с временными метками.
    gap_hours : float, default=1.0
        Порог разрыва между событиями в часах, при превышении которого
        начинается новая сессия.
    sum_cols : tuple[str, ...] | None, default=None
        Числовые столбцы, по которым для каждой сессии нужно посчитать
        сумму. Если None, то суммирование не выполняется.
    last_cols : tuple[str, ...] | None, default=None
        Столбцы, по которым для каждой сессии берётся последнее по
        времени значение. Если None, то такие агрегаты не считаются.
    session_col : str, default="session_id"
        Название столбца с идентификатором сессии в результирующем
        DataFrame.

    Examples
    --------
    >>> import pandas as pd
    >>> from ts_features_sculptor import TimeGapSessionizer
    >>>
    >>> df = pd.DataFrame({
    ...     "time": pd.to_datetime([
    ...         "2025-01-01 10:00:00",
    ...         "2025-01-01 10:30:00",
    ...         "2025-01-01 12:00:00",
    ...         "2025-01-01 12:20:00",
    ...     ]),
    ...     "value": [10, 5, 7, 3],
    ... })
    >>> sessionizer = TimeGapSessionizer(
    ...     gap_hours=1.0,
    ...     time_col="time",
    ...     sum_cols=("value",),
    ... )
    >>> result_df = sessionizer.fit_transform(df)
    >>> print(result_df.to_string(index=False))
                   time  session_id  value
    2025-01-01 10:00:00           0     15
    2025-01-01 12:00:00           1     10
    """

    time_col: str = "time"
    gap_hours: float = 1.0
    sum_cols: tuple[str, ...] | None = None
    last_cols: tuple[str, ...] | None = None
    session_col: str = "session_id"

    def __post_init__(self) -> None:
        if self.gap_hours <= 0:
            raise ValueError(
                "TimeGapSessionizer: gap_hours должно быть положительным."
            )
        if self.sum_cols is None:
            self.sum_cols = tuple()
        if self.last_cols is None:
            self.last_cols = tuple()

    def fit(self, X: pd.DataFrame, y=None):
        self._validate_time_column(X)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self._validate_time_column(X)

        df = X.copy()

        if df.empty:
            return df

        required_cols = set(self.sum_cols) | set(self.last_cols)
        if required_cols:
            missing = required_cols - set(df.columns)
            if missing:
                missing_str = ", ".join(sorted(missing))
                raise ValueError(
                    "TimeGapSessionizer: во входном DataFrame отсутствуют "
                    f"столбцы: {missing_str}"
                )

        times = df[self.time_col]

        # Разрыв между соседними событиями в часах
        delta_hours = times.diff().dt.total_seconds().div(3600.0).fillna(0.0)

        # Новая сессия начинается, если разрыв превышает порог
        new_session = (delta_hours > self.gap_hours).astype("int64")
        session_ids = new_session.cumsum()

        df[self.session_col] = session_ids

        agg_spec: dict[str, str] = {self.time_col: "min"}
        for col in self.sum_cols:
            agg_spec[col] = "sum"
        for col in self.last_cols:
            agg_spec[col] = "last"

        grouped = df.groupby(self.session_col, sort=True, as_index=False).agg(agg_spec)

        grouped[self.session_col] = grouped[self.session_col].astype("int64")

        cols = [self.time_col, self.session_col] + list(self.sum_cols) + list(self.last_cols)
        grouped = grouped[cols]

        return grouped
