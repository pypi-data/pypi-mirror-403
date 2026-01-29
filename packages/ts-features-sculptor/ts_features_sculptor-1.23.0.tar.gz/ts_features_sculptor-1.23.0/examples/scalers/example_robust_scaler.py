import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from ts_features_sculptor import (
    ToDateTime,
    SortByTime,
    Tte,
    RobustLogScaler,
)

t1 = pd.to_datetime("2025-01-01 10:10")

df_raw = pd.DataFrame({
    "time": [
        t1,
        t1 + pd.to_timedelta(1, unit='D'),
        t1 + pd.to_timedelta(1 + 0.00001, unit='D'),
        t1 + pd.to_timedelta(1 + 0.00002, unit='D'),
        t1 + pd.to_timedelta(1 + 10 + 10, unit='D'),
        t1 + pd.to_timedelta(1 + 10 + 10 , unit='D'),
        t1 + pd.to_timedelta(1 + 10 + 10 + 10, unit='D'),
    ],
    "customer_id": ["A"] * 7,
    "merchant_id": ["X"] * 7,
    "value": [100] * 7,
})

pipe = Pipeline([
    ("dt",  ToDateTime(time_col="time")),
    ("sort",  SortByTime(time_col="time")),
    ("tte",   Tte(time_col="time", tte_col="tte")),
    ("scale", RobustLogScaler(
        feature_col="tte",
        out_col="tte_z",
        add_eps=1e-2,
        lookback=5,
        keep_params=False
    )),
])



df_feat = pipe.fit_transform(df_raw)

print(pipe.named_steps["scale"]._median_series_)


print("\n=== После RobustLogScaler ===")
print(df_feat.to_string(index=False))

# обратное преобразование
z_pred = df_feat["tte_z"].values
scaler = pipe.named_steps["scale"]
tte_back = scaler.inverse_transform(z_pred)

df_check = df_feat.copy()
df_check["tte_back"] = tte_back
print("\n=== Обратное преобразование ===")
print(df_check.to_string(index=False))
