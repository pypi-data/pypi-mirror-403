from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from .time_validator import TimeValidator


AggFunc = Union[str, Callable[[pd.Series], Any]]


def _default_bucket_name(freq: str) -> str:
    f = str(freq).upper()
    if f in ("D", "1D"):
        return "daily"
    if f.startswith("W"):
        return "weekly"
    if f in ("MS", "M"):
        return "monthly"
    if f in ("QS", "Q"):
        return "quarterly"
    if f in ("YS", "Y", "AS", "A"):
        return "yearly"
    return "bucket"


def _agg_name(agg: AggFunc) -> str:
    if isinstance(agg, str):
        return agg
    return getattr(agg, "__name__", "agg")


@dataclass
class TimeBucketAggregator(BaseEstimator, TransformerMixin, TimeValidator):
    """
    Агрегирует событийный ряд частоты `freq`.

    time_col, str, default = "time"
      Имя колонки с временными метками
    freq, str, default = "D"
      Частота аггрегации.
    bucket_name: Optional[str] = None
      Префикс для названия колонки с аггрегацией.
    agg_map: Dict[str, Union[AggFunc, List[AggFunc]]], default = dict
      Схема аггрегации.

    Выходные имена:
      {bucket_name}_{field}_{agg_name}

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     "time": pd.to_datetime([
    ...         "2025-01-01 10:00:00",
    ...         "2025-01-01 12:00:00",
    ...         "2025-01-03 09:00:00",
    ...     ]),
    ...     "total": [100.0, 50.0, 30.0],
    ... }).sort_values("time")
    >>> agg = TimeBucketAggregator(
    ...     time_col="time",
    ...     freq="D",
    ...     bucket_name="daily",
    ...     agg_map={"total": "sum", "n": "size"},
    ... )
    >>> result_df = agg.transform(df)
    >>> print(result_df.to_string(index=False))
          time  daily_total_sum  daily_n_size
    2025-01-01            150.0             2
    2025-01-03             30.0             1
    """

    time_col: str = "time"
    freq: str = "D"
    bucket_name: Optional[str] = None
    agg_map: Dict[str, Union[AggFunc, List[AggFunc]]] = field(
        default_factory=dict)

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self._validate_time_column(X)
        if not self.agg_map:
            raise ValueError("TimeBucketAggregator: agg_map не задан")

        df = X.copy()
        if df.empty:
            out_cols = [self.time_col]
            bname = self.bucket_name or _default_bucket_name(self.freq)
            for field, aggs in self.agg_map.items():
                aggs_list = aggs if isinstance(aggs, list) else [aggs]
                for agg in aggs_list:
                    out_cols.append(f"{bname}_{field}_{_agg_name(agg)}")
            return pd.DataFrame(columns=out_cols)

        bname = self.bucket_name or _default_bucket_name(self.freq)

        bucket = df[self.time_col].dt.floor(self.freq)
        g = df.groupby(bucket, sort=True)

        out = pd.DataFrame({self.time_col: g.size().index})

        for field, aggs in self.agg_map.items():
            aggs_list = aggs if isinstance(aggs, list) else [aggs]
            for agg in aggs_list:
                col = f"{bname}_{field}_{_agg_name(agg)}"
                if isinstance(agg, str) and agg == "size":
                    out[col] = g.size().to_numpy()
                    continue
                if field not in df.columns:
                    raise ValueError(
                        f"TimeBucketAggregator: нет колонки {field} "
                        f"для проведения агрегации {_agg_name(agg)}")
                out[col] = g[field].agg(agg).to_numpy()

        return out.reset_index(drop=True)
