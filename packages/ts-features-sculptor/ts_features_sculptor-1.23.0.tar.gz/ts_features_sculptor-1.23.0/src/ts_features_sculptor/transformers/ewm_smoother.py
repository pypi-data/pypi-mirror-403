import pandas as pd
from dataclasses import dataclass
from sklearn.base import BaseEstimator, TransformerMixin

from .time_validator import TimeValidator


@dataclass
class EwmSmoother(BaseEstimator, TransformerMixin, TimeValidator):
    """
    Экспоненциальное сглаживание EWM (N проходов).

    Parameters
    ----------
    time_col : str, default="time"
        Колонка с datetime.
    value_col : str, default="value"
        Колонка с числовым рядом для сглаживания.
    alpha : float, default=0.5
        Параметр EWM alpha (0 < alpha <= 1).
    adjust : bool, default=False
        Параметр adjust для pandas Series.ewm(...).
    passes : int, default=1
        Число последовательных проходов EWM.
    fillna_value : float | None, default=0.0
        Если не None, заполняет NaN в value_col до сглаживания.
    out_col : str, default="value_ewm"
        Имя выходной колонки.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame(
    ...     {
    ...         "time": pd.to_datetime(
    ...             ["2025-01-01", "2025-01-02", "2025-01-03"]
    ...         ),
    ...         "value": [10.0, 0.0, 30.0],
    ...     }
    ... ).sort_values("time")
    >>> tr = EwmSmoother(
    ...     time_col="time",
    ...     value_col="value",
    ...     alpha=0.5,
    ...     passes=2,
    ...     out_col="value_ewm2",
    ... )
    >>> result_df = tr.transform(df)
    >>> print(result_df.round(3).to_string(index=False))
          time  value  value_ewm2
    2025-01-01   10.0        10.0
    2025-01-02    0.0         7.5
    2025-01-03   30.0        12.5
    """

    time_col: str = "time"
    value_col: str = "value"
    alpha: float = 0.5
    adjust: bool = False
    passes: int = 1
    fillna_value: float | None = 0.0
    out_col: str = "value_ewm"

    def __post_init__(self):
        self.alpha = float(self.alpha)
        self.passes = int(self.passes)

    def fit(self, X: pd.DataFrame, y=None):
        self._validate_time_column(X)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self._validate_time_column(X)
        if X.empty:
            return X.copy()

        if self.value_col not in X.columns:
            raise ValueError(
                f"EwmSmoother: missing column {self.value_col!r}"
            )

        df = X.copy()
        s = pd.to_numeric(df[self.value_col], errors="coerce").astype(float)
        if self.fillna_value is not None:
            s = s.fillna(float(self.fillna_value))

        out = s
        for _ in range(self.passes):
            out = out.ewm(alpha=self.alpha, adjust=self.adjust).mean()
        df[self.out_col] = out
        return df
