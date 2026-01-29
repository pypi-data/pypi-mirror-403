from dataclasses import dataclass
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from .time_validator import TimeValidator


@dataclass(kw_only=True)
class FutureWindowTarget(BaseEstimator, TransformerMixin, TimeValidator):
    """
    Трансформер для построения признака-цели как суммы значения метрики
    в будущем окне фиксированной длины.

    Для каждой временной точки t строится:

      Y_h(t) = sum_{k=1..h} value(t+k)

    Текущая точка t не входит в таргет (исключение утечки данных).

    Дополнительно строятся:
      - маска наблюдаемости окна: observed(t)=1, если доступно полное
        окно t+1..t+h,
      - бинарная цель: pos(t)=1{Y_h(t) > pos_threshold},
        а для observed=0 значение pos устанавливается в NA.

    Входной DataFrame должен быть предварительно отсортирован
    по time_col.

    Parameters
    ----------
    value_col : str
        Числовая метрика для суммирования (обязательный параметр).
    horizon_days : int
        Горизонт (число шагов вперёд; для дневной сетки это число дней).
    time_col : str, default="time"
        Название столбца со временными метками.
    fillna_value : float | None, default=0.0
        Значение для заполнения NaN в `value_col` перед расчётом.
    out_target_col : str | None, default=None
        Имя выходного столбца суммы. При None используется "Y{h}".
    out_pos_col : str | None, default=None
        Имя выходного бинарного таргета. При  None используется
        "Y{h}_pos".
    out_observed_col : str | None, default=None
        Имя маски наблюдаемости. При None используется "Y{h}_observed".
    pos_threshold : float, default=0.0
        Порог для бинаризации.

    Examples
    --------
    >>> import pandas as pd
    >>> from ts_features_sculptor import FutureWindowTarget
    >>> df = pd.DataFrame({
    ...   "time": pd.to_datetime([
    ...     "2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04",
    ...     "2025-01-05"
    ...   ]),
    ...   "daily_value": [0.0, 10.0, 0.0, 5.0, 7.0],
    ... })
    >>> tr = FutureWindowTarget(
    ...   value_col="daily_value",
    ...   horizon_days=3,
    ...   time_col="time",
    ...   out_target_col="Y3",
    ...   out_pos_col="Y3_pos",
    ...   out_observed_col="Y3_observed",
    ... )
    >>> result_df = tr.fit_transform(df)
    >>> print(result_df.to_string(index=False))  # doctest: +NORMALIZE_WHITESPACE
          time  daily_value   Y3  Y3_pos  Y3_observed
    2025-01-01          0.0 15.0       1            1
    2025-01-02         10.0 12.0       1            1
    2025-01-03          0.0  NaN    <NA>            0
    2025-01-04          5.0  NaN    <NA>            0
    2025-01-05          7.0  NaN    <NA>            0
    """

    value_col: str
    horizon_days: int

    time_col: str = "time"
    fillna_value: float | None = 0.0

    out_target_col: str | None = None
    out_pos_col: str | None = None
    out_observed_col: str | None = None
    pos_threshold: float = 0.0

    def __post_init__(self) -> None:
        if self.value_col is None or str(self.value_col).strip() == "":
            raise ValueError(
                "FutureWindowTarget: отсуствует value_col.")
        if int(self.horizon_days) <= 0:
            raise ValueError(
                "FutureWindowTarget: horizon_days должен быть > 0.")
        self.horizon_days = int(self.horizon_days)

        if self.out_target_col is None:
            self.out_target_col = f"Y{self.horizon_days}"
        if self.out_observed_col is None:
            self.out_observed_col = f"Y{self.horizon_days}_observed"
        if self.out_pos_col is None:
            self.out_pos_col = f"Y{self.horizon_days}_pos"

    def fit(self, X: pd.DataFrame, y=None):
        self._validate_time_column(X)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self._validate_time_column(X)
        if self.value_col not in X.columns:
            raise ValueError(
                f"FutureWindowTarget: нет колонки '{self.value_col}'.")

        df = X.copy()

        v = pd.to_numeric(df[self.value_col], errors="coerce")
        if self.fillna_value is not None:
            v = v.fillna(float(self.fillna_value))

        cs = v.cumsum()
        cs_fwd = cs.shift(-self.horizon_days)

        y_sum = cs_fwd - cs
        observed = cs_fwd.notna()

        df[self.out_target_col] = y_sum.astype("float32")

        if self.out_pos_col is not None:
            pos = (
                df[self.out_target_col] > float(self.pos_threshold)
            ).astype("Int8")
            pos[~observed] = pd.NA
            df[self.out_pos_col] = pos

        df[self.out_observed_col] = observed.astype("int8")
        return df
