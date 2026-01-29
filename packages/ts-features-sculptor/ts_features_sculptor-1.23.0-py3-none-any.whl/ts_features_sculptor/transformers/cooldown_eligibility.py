from __future__ import annotations

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class CooldownEligibility(BaseEstimator, TransformerMixin):
    """
    Выполняет вычисление признаков допустимости применения воздействия
    при наличии периода, когда событие практически не может произойти
    из-за ограничений на частоту воздействия:

      event_flag_lag = event_flag(t-1)
      cooldown_ok = (days_since_last_end >= cooldown_days) OR
                    (NaN -> True, если nan_means_ok)
      eligible_pre = (event_flag_lag == 0) & cooldown_ok

    Примечание:
      Маркеры первого/последнего тика события рекомендуется получать
      на шаге врезки интервалов (IntervalEventsMerge:
      `{event_name}_start_flag`, `{event_name}_end_flag`).

    Parameters
    ----------
    event_flag_col : str
        название столбца с флагом события
    days_since_last_end_col : str
        название столбца с числом дней от последнего события

    Examples
    --------
      >>> import pandas as pd
      >>> df = pd.DataFrame({
      ...   "time": pd.to_datetime([
      ...       "2025-01-10",
      ...       "2025-01-11",
      ...       "2025-01-12",
      ...       "2025-01-13",
      ...       "2025-01-14",
      ...       "2025-01-15",
      ...       "2025-01-16",
      ...   ]),
      ...   "event_flag": [0, 0, 1, 1, 0, 0, 0],
      ...   "days_since_last_event_end": [pd.NA, pd.NA, pd.NA, pd.NA, 1, 2, 3],
      ... })
      >>> transformer = CooldownEligibility(
      ...   event_flag_col="event_flag",
      ...   days_since_last_end_col="days_since_last_event_end",
      ...   cooldown_days=2,
      ... )
      >>> result_df = transformer.fit_transform(df)
      >>> print(result_df.to_string(index=False))
            time  event_flag days_since_last_event_end  event_flag_lag1  cooldown_ok  eligible_pre
      2025-01-10           0                      <NA>              NaN         True          True
      2025-01-11           0                      <NA>              0.0         True          True
      2025-01-12           1                      <NA>              0.0         True          True
      2025-01-13           1                      <NA>              1.0         True         False
      2025-01-14           0                         1              1.0        False         False
      2025-01-15           0                         2              0.0         True          True
      2025-01-16           0                         3              0.0         True          True
    """

    def __init__(
        self,
        event_flag_col: str,
        days_since_last_end_col: str,
        cooldown_days: float = 30.0,
        lag: int = 1,
        time_col: str = "time",
        assume_sorted: bool = True,
        nan_means_ok: bool = True,
        out_event_flag_lag_col: str | None = None,
        out_cooldown_ok_col: str = "cooldown_ok",
        out_eligible_pre_col: str = "eligible_pre",
    ):
        self.event_flag_col = event_flag_col
        self.days_since_last_end_col = days_since_last_end_col
        self.cooldown_days = float(cooldown_days)
        self.lag = int(lag)
        self.time_col = time_col
        self.assume_sorted = bool(assume_sorted)
        self.nan_means_ok = bool(nan_means_ok)
        self.out_event_flag_lag_col = out_event_flag_lag_col
        self.out_cooldown_ok_col = out_cooldown_ok_col
        self.out_eligible_pre_col = out_eligible_pre_col

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()

        if not self.assume_sorted:
            df = df.sort_values([self.time_col], kind="mergesort")

        lag_col = (
            self.out_event_flag_lag_col
            if self.out_event_flag_lag_col
            else f"{self.event_flag_col}_lag{self.lag}"
        )
        df[lag_col] = df[self.event_flag_col].shift(self.lag)

        dsl = df[self.days_since_last_end_col]
        cooldown_ok = dsl >= self.cooldown_days
        if self.nan_means_ok:
            cooldown_ok = cooldown_ok | dsl.isna()

        df[self.out_cooldown_ok_col] = cooldown_ok.astype(bool)

        prev_inactive = df[lag_col].fillna(0) == 0
        df[self.out_eligible_pre_col] = (
            prev_inactive & df[self.out_cooldown_ok_col]
        ).astype(bool)

        return df
