import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from .time_validator import TimeValidator

@dataclass
class DateTimeDecomposer(BaseEstimator, 
                         TransformerMixin, 
                         TimeValidator):
    """
    Декомпозиция значений из столбца с временными метками.

    Можно вычислить сдежующие признаки, указав их в features:
      - year год
      - month месяц
      - day день
      - day_of_week день недели (0=понедельник, 6=воскресенье)
      - is_weekend 1, если день недели — суббота или воскресенье
      - hour час в виде вещественного числа (с учётом минут и секунд)
      - minute минуты
      - second секунды
      - day_of_week_sin синус циклического преобразования дня недели
      - day_of_week_cos косинус циклического преобразования дня недели
      - hour_sin синус циклического преобразования часа
      - hour_cos косинус циклического преобразования часа
      - is_friday 1, если день недели — пятница, иначе 0
      - is_night 1, если час (целый) от 0 до 5, иначе 0
      - is_morning 1, если час от 6 до 11, иначе 0
      - is_afternoon 1, если час от 12 до 17, иначе 0
      - is_evening 1, если час от 18 до 23, иначе 0
      - day_of_year номер дня в году
      - week_of_year номер недели года (ISO календарь)
      - quarter номер квартала
      - hour_int целочисленный час
      - hour_bucket_{k} дискретизация часа по шагу k часов
      - is_monday 1, если день недели — понедельник, иначе 0
      - is_month_start 1, если дата первый день месяца
      - is_month_end 1, если дата последний день месяца
      - is_quarter_start 1, если дата первый день квартала
      - is_quarter_end 1, если дата последний день квартала
      - is_year_start 1, если дата 1 января
      - is_year_end 1, если дата 31 декабря
      - month_name название месяца
      - day_name название дня недели

    Parameters
    ----------
    time_col : str, default='time'
        Название столбца с временными метками.
    features : list[str], optional
        Список признаков для извлечения.

    Methods
    -------
    fit(X, y=None)
        Не используется, возвращает self.
    transform(X)
        Вычисляет и добавляет столбцы с компонентами временной метки 
        в DataFrame.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'time': ['2023-06-15 08:30:00']})
    >>> df['time'] = pd.to_datetime(df['time'])
    >>> transformer = DateTimeDecomposer(
    ...     time_col='time',
    ...     features=['year', 'month', 'day', 'hour_bucket_12']
    ... )
    >>> result = transformer.transform(df)
    >>> print(result.to_string(index=False))
                   time  year  month  day  hour_bucket_12
    2023-06-15 08:30:00  2023      6   15               0
    """
    
    time_col: str = 'time'
    features: List[str] = field(default_factory=lambda: [
        "year", "month", "day", "day_of_week", "is_weekend", "hour",
        "minute", "second", "day_of_week_sin", "day_of_week_cos",
        "hour_sin", "hour_cos", "is_friday", "is_night", "is_morning",
        "is_afternoon", "is_evening", "day_of_year", "week_of_year",
        "quarter", "hour_int", "is_monday"
    ])

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self._validate_time_column(X)

        known_features = {
            "year", "month", "day", "day_of_week", "is_weekend", "hour",
            "minute", "second", "day_of_week_sin", "day_of_week_cos",
            "hour_sin", "hour_cos", "is_friday", "is_night", "is_morning",
            "is_afternoon", "is_evening", "day_of_year", "week_of_year",
            "quarter", "hour_int", "is_monday", "is_month_start",
            "is_month_end", "is_quarter_start", "is_quarter_end",
            "is_year_start", "is_year_end", "month_name", "day_name"
        }

        # dynamic hour_bucket_{k}
        dynamic_hour_bucket_features = [
            f for f in self.features if f.startswith("hour_bucket_")
        ]
        static_features = [
            f for f in self.features if not f.startswith("hour_bucket_")
        ]

        unknown_static = set(static_features) - known_features

        if unknown_static:
            raise ValueError(
                f"DateTimeDecomposer: неизвестные features {unknown_static}"
            )

        hour_bucket_sizes: list[int] = []
        bad_hour_bucket_features: list[str] = []
        for f in dynamic_hour_bucket_features:
            suffix = f[len("hour_bucket_"):]
            if not suffix.isdigit():
                bad_hour_bucket_features.append(f)
                continue
            k = int(suffix)
            if k < 1 or k > 24:
                bad_hour_bucket_features.append(f)
                continue
            hour_bucket_sizes.append(k)

        if bad_hour_bucket_features:
            raise ValueError(
                "DateTimeDecomposer: неверные features "
                f"{bad_hour_bucket_features}. "
                f"Ожидается hour_bucket_{{k}}, где 1<=k<=24"
            )

        hour_bucket_sizes = sorted(set(hour_bucket_sizes))

        if not self.features:
            raise ValueError("DateTimeDecomposer: список features пуст.")

        result_df = X.copy()

        if "year" in self.features:
            result_df["year"] = result_df[self.time_col].dt.year
        if "month" in self.features:
            result_df["month"] = result_df[self.time_col].dt.month
        if "day" in self.features:
            result_df["day"] = result_df[self.time_col].dt.day
        
        day_of_week_features = [
            "day_of_week", "is_weekend", "day_of_week_sin", 
            "day_of_week_cos", "is_friday", "is_monday"
        ]
        if any(f in self.features for f in day_of_week_features):
            day_of_week = result_df[self.time_col].dt.dayofweek
            if "day_of_week" in self.features:
                result_df["day_of_week"] = day_of_week
            if "is_weekend" in self.features:
                result_df["is_weekend"] = (day_of_week >= 5).astype(int)
            if "day_of_week_sin" in self.features:
                result_df["day_of_week_sin"] = np.sin(
                    day_of_week * (2 * np.pi / 7))
            if "day_of_week_cos" in self.features:
                result_df["day_of_week_cos"] = np.cos(
                    day_of_week * (2 * np.pi / 7))
            if "is_friday" in self.features:
                result_df["is_friday"] = (day_of_week == 4).astype(int)
            if "is_monday" in self.features:
                result_df["is_monday"] = (day_of_week == 0).astype(int)

        hour_features = ["hour", "hour_sin", "hour_cos"]
        if any(f in self.features for f in hour_features):
            hour_decimal = (result_df[self.time_col].dt.hour +
                            result_df[self.time_col].dt.minute / 60. +
                            result_df[self.time_col].dt.second / 3600.)
            if "hour" in self.features:
                result_df["hour"] = hour_decimal
            if "hour_sin" in self.features:
                result_df["hour_sin"] = np.sin(
                    hour_decimal * (2 * np.pi / 24))
            if "hour_cos" in self.features:
                result_df["hour_cos"] = np.cos(
                    hour_decimal * (2 * np.pi / 24))
        
        if "hour_int" in self.features:
            result_df["hour_int"] = result_df[self.time_col].dt.hour \
                .astype(int)

        if hour_bucket_sizes:
            hour_int_for_bucket = result_df[self.time_col].dt.hour.astype(int)
            for k in hour_bucket_sizes:
                col = f"hour_bucket_{k}"
                result_df[col] = (hour_int_for_bucket // k * k).astype(int)

        if "minute" in self.features:
            result_df["minute"] = result_df[self.time_col].dt.minute
        if "second" in self.features:
            result_df["second"] = result_df[self.time_col].dt.second

        time_of_day_features = [
            "is_night", "is_morning", "is_afternoon", "is_evening"]
        if any(f in self.features for f in time_of_day_features):
            hour_int = result_df[self.time_col].dt.hour
            if "is_night" in self.features:
                result_df["is_night"] = hour_int.between(0, 5).astype(int)
            if "is_morning" in self.features:
                result_df["is_morning"] = hour_int.between(6, 11).astype(int)
            if "is_afternoon" in self.features:
                result_df["is_afternoon"] = hour_int.between(12, 17) \
                    .astype(int)
            if "is_evening" in self.features:
                result_df["is_evening"] = hour_int.between(18, 23).astype(int)

        if "day_of_year" in self.features:
            result_df["day_of_year"] = result_df[self.time_col].dt.dayofyear
        if "week_of_year" in self.features:
            result_df["week_of_year"] = result_df[self.time_col].dt \
                .isocalendar().week.astype(int)
        if "quarter" in self.features:
            result_df["quarter"] = result_df[self.time_col].dt.quarter

        if "is_month_start" in self.features:
            result_df["is_month_start"] = result_df[self.time_col].dt \
                .is_month_start.astype(int)
        if "is_month_end" in self.features:
            result_df["is_month_end"] = result_df[self.time_col].dt \
                .is_month_end.astype(int)
        if "is_quarter_start" in self.features:
            result_df["is_quarter_start"] = result_df[self.time_col].dt \
                .is_quarter_start.astype(int)
        if "is_quarter_end" in self.features:
            result_df["is_quarter_end"] = result_df[self.time_col].dt \
                .is_quarter_end.astype(int)
        if "is_year_start" in self.features:
            result_df["is_year_start"] = result_df[self.time_col].dt \
                .is_year_start.astype(int)
        if "is_year_end" in self.features:
            result_df["is_year_end"] = result_df[self.time_col].dt \
                .is_year_end.astype(int)
        if "month_name" in self.features:
            result_df["month_name"] = result_df[self.time_col].dt.month_name()
        if "day_name" in self.features:
            result_df["day_name"] = result_df[self.time_col].dt.day_name()

        return result_df
