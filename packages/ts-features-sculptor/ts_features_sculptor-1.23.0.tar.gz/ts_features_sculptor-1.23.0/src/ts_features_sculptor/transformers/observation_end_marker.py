import pandas as pd
from dataclasses import dataclass
from sklearn.base import BaseEstimator, TransformerMixin
from .time_validator import TimeValidator


@dataclass
class ObservationEndMarker(BaseEstimator, TransformerMixin, TimeValidator):
    """
    Трансформер для фиксации последнего момента наблюдения таймсерии
    с учётом конца окна наблюдений для группы.

    Делает две вещи:
    1) Для последней строки пересчитывает TTE как
       (obs_end_time - last_time) в днях.
    2) Помечает последнюю строку как право-цензурированную
       (is_censored=1, censor_type="observation_end"), оставляя все
       предыдущие строки без изменений. Таким образом:
       - строки с is_censored=0 интерпретируются как «событие наблюдалось»
         (не выжил),
       - последняя строка с is_censored=1 — как правая цензура.

    Parameters
    ----------
    obs_end_time : pd.Timestamp или str
        Конец окна наблюдений для группы (например, конец датасета
        по мерчанту). Должен быть не раньше максимального значения
        в колонке `time_col`.
    time_col : str, default="time"
        Название колонки с временными метками (datetime).
    tte_col : str, default="tte"
        Название столбца с TTE (в днях), который нужно скорректировать
        для последней строки.
    censor_flag_col : str, default="is_censored"
        Название столбца с флагом цензурирования (0/1). Если столбца нет,
        он будет создан и заполнен нулями.
    censor_type_col : str, default="censor_type"
        Название столбца с типом цензуры. Если столбца нет, он будет
        создан и заполнен pd.NA.
    observation_end_label : str, default="observation_end"
        Значение, которое будет записано в `censor_type_col` для
        последней строки.

    Examples
    --------
    >>> import pandas as pd
    >>> from ts_features_sculptor import ObservationEndMarker
    >>>
    >>> df = pd.DataFrame({
    ...     "time": pd.to_datetime([
    ...         "2025-01-01 10:00:00",
    ...         "2025-01-05 10:00:00",
    ...         "2025-01-10 10:00:00",
    ...     ]),
    ...     "tte": [4.0, 5.0, float("nan")]
    ... })
    >>> marker = ObservationEndMarker(
    ...     obs_end_time="2025-02-01 10:00:00",
    ...     time_col="time",
    ... )
    >>> result_df = marker.fit_transform(df)
    >>> print(result_df.to_string(index=False))
                       time  tte
    2025-01-01 10:00:00  4.0
    2025-01-05 10:00:00  5.0
    2025-01-10 10:00:00 22.0
    """

    time_col: str = "time"
    tte_col: str = "tte"
    obs_end_time: pd.Timestamp | str | None = None
    censor_flag_col: str = "is_censored"
    censor_type_col: str = "censor_type"
    observation_end_label: str = "observation_end"

    def __post_init__(self) -> None:
        if self.obs_end_time is None:
            raise ValueError(
                "ObservationEndMarker: obs_end_time должен быть задан."
            )

    def fit(self, X: pd.DataFrame, y=None):
        self._validate_time_column(X)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self._validate_time_column(X)

        df = X.copy()

        if self.tte_col not in df.columns:
            raise ValueError(
                f"ObservationEndMarker: столбец '{self.tte_col}' "
                "отсутствует во входном DataFrame."
            )

        times = df[self.time_col]
        obs_end = pd.to_datetime(self.obs_end_time)

        if (times > obs_end).any():
            raise ValueError(
                "ObservationEndMarker: обнаружены значения time_col "
                "позже obs_end_time."
            )

        # Гарантируем наличие колонок цензурирования
        if self.censor_flag_col not in df.columns:
            df[self.censor_flag_col] = 0
        if self.censor_type_col not in df.columns:
            df[self.censor_type_col] = pd.NA

        last_idx = df.index[-1]
        last_time = times.loc[last_idx]
        delta_days = (obs_end - last_time).total_seconds() / 86400.0

        if delta_days < 0:
            raise ValueError(
                "ObservationEndMarker: obs_end_time меньше последнего "
                "значения time_col (delta_days < 0)."
            )

        # Обновляем TTE для последней строки
        df.loc[last_idx, self.tte_col] = float(delta_days)

        # Помечаем последнюю строку как право-цензурированную
        df.loc[last_idx, self.censor_flag_col] = 1
        df.loc[last_idx, self.censor_type_col] = self.observation_end_label

        return df
