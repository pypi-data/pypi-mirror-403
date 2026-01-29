"""
Разметка эпизодов, правое цензурирование по времени наблюдения и
построение таргета outflow (событие «отсутствовал не меньше tau_days и
возврата не было») для анализа выживаемости.
"""

import pandas as pd
from sklearn.pipeline import Pipeline

from ts_features_sculptor import (
    ToDateTime,
    SortByTime,
    TimeGapSessionizer,
    Tte,
    EpisodeSplitter,
    ObservationEndMarker,
    OutflowTarget,
)

df = pd.DataFrame({
    "time": [
        "2025-01-01 10:00:00",
        "2025-01-01 10:10:00",
        "2025-01-10 10:00:00",
        "2025-03-20 10:00:00",
        "2025-03-25 10:00:00",
    ],
    "value": [10, 40, 50, 50, 50],
})

# Конец окна наблюдения для группы (например, мерчанта)
obs_end_time = "2025-04-01 10:00:00"

# Порог отсутствия, относительно которого определяем outflow
tau_days = 30.0

pipeline = Pipeline([
    ("to_datetime", ToDateTime(time_col="time")),
    ("sort_by_time", SortByTime(time_col="time")),
    ("sessions", TimeGapSessionizer(
        time_col="time",
        gap_hours=0.5,
        sum_cols=("value",),
    )),
    ("tte", Tte(time_col="time", tte_col="tte")),
    ("episodes", EpisodeSplitter(
        time_col="time",
        tau_days=tau_days,
        episode_col="episode",
        censor_type_col="censor_type",
        censor_flag_col="is_censored",
        obs_end_time=obs_end_time,
    )),
    # Если EpisodeSplitter уже врезает tte до obs_end_time и размечает
    # observation_end, ObservationEndMarker можно не использовать.
    # Если в твоей версии это не так, оставляем:
    ("obs_end_marker", ObservationEndMarker(
        time_col="time",
        tte_col="tte",
        obs_end_time=obs_end_time,
        censor_flag_col="is_censored",
        censor_type_col="censor_type",
        observation_end_label="observation_end",
    )),
    ("outflow_target", OutflowTarget(
        tte_col="tte",
        censor_flag_col="is_censored",
        tau_days=tau_days,
        duration_col="duration_outflow",
        event_col="event_outflow",
    )),
])

result_df = pipeline.fit_transform(df)

print(result_df[[
    "time",
    "tte",
    "episode",
    "censor_type",
    "is_censored",
    "duration_outflow",
    "event_outflow",
]].to_string(index=False))
