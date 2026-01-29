import pandas as pd
from dataclasses import dataclass
from sklearn.base import BaseEstimator, TransformerMixin
from .time_validator import TimeValidator


@dataclass
class EpisodeSplitter(BaseEstimator, TransformerMixin, TimeValidator):
    """
    Трансформер для разбиения последовательности событий на эпизоды
    по временным разрывам в активности объекта. Новый эпизод создается,
    если разрыв превышает порог `tau_days`.

    Дополнительно помечает строки, на которых эпизод заканчивается:
      * конец эпизода (разрыв > tau_days) — отдельной меткой,
      * конец данных (последняя строка) — своей меткой,
      * добавляет бинарный флаг цензурирования (0/1).

    Parameters
    ----------
    time_col : str, default="time"
        Название колонки с временными метками (datetime).
    tau_days : float, default=60.0
        Порог разрыва по времени в днях. Если разрыв между соседними
        событиями больше этого значения, начинается новый эпизод.
    episode_col : str, default="episode_no"
        Название выходной колонки с номером эпизода (начиная с 0).
    censor_type_col : str, default="censor_type"
        Название колонки с типом окончания эпизода для строк,
        где эпизод заканчивается. Для остальных строк значение <NA>.
    censor_flag_col : str, default="is_censored"
        Название колонки с бинарным флагом цензурирования:
        1 — строка является концом эпизода или концом наблюдений,
        0 — внутри эпизода (есть следующий визит в том же эпизоде).
    episode_end_label : str, default="episode_end"
        Метка причины окончания эпизода, когда следующий визит
        начинается после разрыва > tau_days.
    obs_end_label : str, default="observation_end"
        Метка причины окончания для последней строки данных (конец наблюдений).
    obs_end_time : pd.Timestamp | None, default=None
        Дата/время конца наблюдений для данной таймсерии. Если задана,
        используется только для валидации: проверяется, что все `time_col`
        не позже `obs_end_time`. Метка `obs_end_label` присваивается
        последней строке вне зависимости от конкретного значения obs_end_time.

    Notes
    -----
    * Ожидается, что входной DataFrame уже отсортирован по `time_col`
      (например, через трансформер SortByTime).
    * Группировка по объектам выполняется вне этого трансформера: он рассчитан
      на применение к одной индивидуальной таймсерии.
    * Бинарный флаг цензурирования `censor_flag_col` строится напрямую
      из `censor_type_col`: 1, если тип цензуры проставлен, иначе 0.

    Examples
    --------
    >>> from ts_features_sculptor import EpisodeSplitter
    >>>
    >>> df = pd.DataFrame({
    ...     "time": pd.to_datetime([
    ...         "2025-01-01 10:00:00",
    ...         "2025-01-05 10:00:00",
    ...         "2025-01-10 10:00:00",
    ...         "2025-03-01 10:00:00",
    ...         "2025-03-05 10:00:00",
    ...     ])
    ... })
    >>> splitter = EpisodeSplitter(
    ...     time_col="time",
    ...     tau_days=30,
    ...     episode_col="episode_no",
    ...     censor_type_col="censor_type",
    ...     censor_flag_col="is_censored",
    ... )
    >>> result_df = splitter.fit_transform(df)
    >>> print(result_df.to_string(index=False))  # doctest: +NORMALIZE_WHITESPACE
    time                episode_no censor_type     is_censored
    2025-01-01 10:00:00 0          <NA>           0
    2025-01-05 10:00:00 0          <NA>           0
    2025-01-10 10:00:00 0          episode_end    1
    2025-03-01 10:00:00 1          <NA>           0
    2025-03-05 10:00:00 1          observation_end 1
    """

    time_col: str = "time"
    tau_days: float = 60.0
    episode_col: str = "episode_no"

    censor_type_col: str = "censor_type"
    censor_flag_col: str = "is_censored"
    episode_end_label: str = "episode_end"
    obs_end_label: str = "observation_end"
    obs_end_time: pd.Timestamp | None = None

    def __post_init__(self):
        if self.tau_days <= 0:
            raise ValueError(
                "EpisodeSplitter: tau_days должен быть положительным."
            )

    def fit(self, X: pd.DataFrame, y=None):
        self._validate_time_column(X)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self._validate_time_column(X)

        df = X.copy()

        times = df[self.time_col]

        if self.obs_end_time is not None:
            obs_end = pd.to_datetime(self.obs_end_time)
            if (times > obs_end).any():
                raise ValueError(
                    "EpisodeSplitter: обнаружены значения time_col "
                    "позже obs_end_time."
                )

        gaps_days = times.diff().dt.total_seconds() / 86400.0
        episode_starts = (gaps_days > self.tau_days).fillna(False)
        episodes = episode_starts.cumsum().astype("int64")

        df[self.episode_col] = episodes.to_numpy()

        censor_type = pd.Series(pd.NA, index=df.index, dtype="object")

        episodes_series = pd.Series(episodes, index=df.index)
        last_in_episode = episodes_series.ne(episodes_series.shift(-1))

        last_idx = df.index[-1]

        mask_episode_end = last_in_episode & (df.index != last_idx)
        censor_type.loc[mask_episode_end] = self.episode_end_label

        if self.obs_end_label:
            censor_type.loc[last_idx] = self.obs_end_label
        else:
            censor_type.loc[last_idx] = self.episode_end_label

        df[self.censor_type_col] = censor_type

        censor_flag = pd.Series(0, index=df.index, dtype="int8")
        censor_flag.loc[censor_type.notna()] = 1
        df[self.censor_flag_col] = censor_flag

        return df
