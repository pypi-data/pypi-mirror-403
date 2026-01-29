import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from sklearn.base import BaseEstimator, TransformerMixin
from .time_validator import TimeValidator


def _td_to_days(delta):
    return delta / np.timedelta64(1, "s") / 86_400.0


@dataclass
class EventDaysFeatures(BaseEstimator, TransformerMixin, TimeValidator):
    """
    Трансформер для вычисления временных характеристик относительно
    интервальных событий.

    Добавляет инженерные признаки (настраиваемо через features):
    - days_to_next_{event_name} дней до начала следующего события
      или fillna если следующее событие отсуствует;
    - days_since_last_{event_name}_end дней от окончания события
      или fillna;
    - {event_name}_elapsed_days дней от начала события во время
      события или fillna.
    - days_to_{event_name}_end дней до конца текущего события во время
      события или fillna.
    - {event_name}_duration_days длительность текущего события во время
      события или fillna.

    Parameters
    ----------
    time_col: str, default = "time"
        Название колонки с временной меткой.
    events_df: pd.DataFrame,
               default = field(default_factory=pd.DataFrame)
        DataFrame с интервальными событиями.
    start_col: str, default = "start"
        Название колонки с временем начала события в events_df.
    end_col: str, default = "end"
        Название колонки с временем окончания события в events_df.
    event_name: str, default = "event"
        Название события для формирования названий выходных признаков.
    fillna: float, default  = np.nan
        Значения для заполнения выходных характеристик вне зоны их
        действия.
    features: object, default = None
        Какие признаки добавлять:
        - None или "base": базовые 3 колонки
          ("since_last_end","to_next","elapsed");
        - "all": все доступные ("since_last_end", "to_next", "elapsed",
                                "to_end", "duration");
        - iterable из ключей ("since_last_end", "to_next","elapsed",
                              "to_end", "duration")
          или явных имен колонок.
    duration_inclusive: bool, default = False
        Если True, {event_name}_duration_days включает конечный день
        интервала (полезно для day-grid).

    Examples
    --------
    >>> import pandas as pd
    >>> X = pd.DataFrame({"time": pd.to_datetime([
    ...     "2025-01-01 12:00",   # before promo 1
    ...     "2025-01-02 06:00",   # promo 1 start
    ...     "2025-01-03 12:00",   # promo 1
    ...     "2025-01-04 18:00",   # promo 1 end
    ...     "2025-01-05 00:00",   # after promo 1 before promo 2
    ...     "2025-01-06 12:00",   # after promo 1 before promo 2
    ...     "2025-01-08 06:00",   # promo 2
    ...     "2025-01-10 18:00",   # after promo 2
    ...     "2025-01-15 18:00",   # after promo 2
    ... ])})
    >>> promos = pd.DataFrame({
    ...     "start": pd.to_datetime([
    ...         "2025-01-02 00:00", "2025-01-07 06:00"]),
    ...     "end": pd.to_datetime([
    ...         "2025-01-04 18:00", "2025-01-09 18:00"]),
    ... })
    >>> transformer = EventDaysFeatures(
    ...     time_col="time", events_df=promos, event_name="promo")
    >>> result_df = transformer.transform(X)
    >>> print(result_df.to_string(index=False))
                   time  days_since_last_promo_end  days_to_next_promo  promo_elapsed_days
    2025-01-01 12:00:00                        NaN                0.50                 NaN
    2025-01-02 06:00:00                        NaN                 NaN                0.25
    2025-01-03 12:00:00                        NaN                 NaN                1.50
    2025-01-04 18:00:00                        NaN                 NaN                2.75
    2025-01-05 00:00:00                       0.25                2.25                 NaN
    2025-01-06 12:00:00                       1.75                0.75                 NaN
    2025-01-08 06:00:00                        NaN                 NaN                1.00
    2025-01-10 18:00:00                       1.00                 NaN                 NaN
    2025-01-15 18:00:00                       6.00                 NaN                 NaN
    """

    time_col: str = "time"
    events_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    start_col: str = "start"
    end_col: str = "end"
    event_name: str = "event"
    fillna: float = np.nan

    features: object = None
    duration_inclusive: bool = False

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def _check_events_df(self):
        if self.events_df.empty:
            return
        req = {self.start_col, self.end_col}
        miss = req - set(self.events_df.columns)
        if miss:
            raise ValueError(
                f"EventDaysFeatures: Отсуствуют колонки {miss}")
        bad = (
            self.events_df[self.events_df[self.end_col] <
                           self.events_df[self.start_col]]
        )
        if not bad.empty:
            raise ValueError(
                "EventDaysFeatures: "
                "Найдены события с end < start:\n" + bad.to_string())

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self._validate_time_column(X)
        self._check_events_df()

        X_ = X.copy()
        inclusive_extra = 1.0 if self.duration_inclusive else 0.0

        col_since = f"days_since_last_{self.event_name}_end"
        col_to_next = f"days_to_next_{self.event_name}"
        col_elapsed = f"{self.event_name}_elapsed_days"
        col_to_end = f"days_to_{self.event_name}_end"
        col_duration = f"{self.event_name}_duration_days"

        base_cols = (col_since, col_to_next, col_elapsed)
        all_cols = (
            col_since,
            col_to_next,
            col_elapsed,
            col_to_end,
            col_duration,
        )

        key_map = {
            "since_last_end": col_since,
            "to_next": col_to_next,
            "elapsed": col_elapsed,
            "to_end": col_to_end,
            "duration": col_duration,
        }

        def _resolve_feature(f):
            if f in key_map:
                return key_map[f]
            if f in all_cols:
                return f
            raise ValueError(
                f"EventDaysFeatures: неизвестная фича '{f}'. "
                f"Допустимые ключи: {list(key_map.keys())} или имена колонок."
            )

        if self.features is None:
            _out_cols = list(base_cols)
        elif isinstance(self.features, str):
            s = self.features.strip().lower()
            if s == "base":
                _out_cols = list(base_cols)
            elif s == "all":
                _out_cols = list(all_cols)
            else:
                parts = [
                    p.strip()
                    for p in self.features.split(",")
                    if p.strip()
                ]
                _out_cols = [_resolve_feature(p) for p in parts]
        else:
            _out_cols = [_resolve_feature(p) for p in self.features]

        for c in _out_cols:
            X_[c] = self.fillna

        if self.events_df.empty:
            return X_.reset_index(drop=True)

        intervals = self.events_df.copy()
        intervals = intervals.sort_values(
            self.start_col, kind="mergesort"
        ).reset_index(drop=True)
        starts = intervals[self.start_col].values.astype("datetime64[ns]")
        ends = intervals[self.end_col].values.astype("datetime64[ns]")

        ends_sorted = np.sort(ends)

        t = X_[self.time_col].values.astype("datetime64[ns]")
        n = len(t)

        prev_start_idx = np.searchsorted(starts, t, side="right") - 1
        inside = (
            (prev_start_idx >= 0) &
            (t <= ends[np.clip(prev_start_idx, 0, len(ends)-1)])
        )
        outside = ~inside

        need_elapsed = (col_elapsed in _out_cols)
        need_to_end = (col_to_end in _out_cols)
        need_duration = (col_duration in _out_cols)
        need_to_next = (col_to_next in _out_cols)
        need_since = (col_since in _out_cols)

        if inside.any() and (need_elapsed or need_to_end or need_duration):
            idx_inside = prev_start_idx[inside]

            if need_elapsed:
                elapsed = _td_to_days(t[inside] - starts[idx_inside])
                X_.loc[inside, col_elapsed] = elapsed

            if need_to_end:
                to_end = _td_to_days(ends[idx_inside] - t[inside])
                X_.loc[inside, col_to_end] = to_end

            if need_duration:
                dur = (
                    _td_to_days(ends[idx_inside] - starts[idx_inside]) +
                    inclusive_extra
                )
                X_.loc[inside, col_duration] = dur

        if need_to_next:
            next_start_idx = np.searchsorted(starts, t, side="right")
            mask_next = outside & (next_start_idx < len(starts))
            if mask_next.any():
                delta_next = (
                    _td_to_days(starts[next_start_idx[mask_next]] -
                    t[mask_next])
                )
                X_.loc[mask_next, col_to_next] = delta_next

        if need_since:
            prev_end_idx = np.searchsorted(ends_sorted, t, side="left") - 1
            mask_prev = outside & (prev_end_idx >= 0)
            if mask_prev.any():
                delta_prev = (
                    _td_to_days(t[mask_prev] -
                    ends_sorted[prev_end_idx[mask_prev]])
                )
                X_.loc[mask_prev, col_since] = delta_prev

        return X_.reset_index(drop=True)
