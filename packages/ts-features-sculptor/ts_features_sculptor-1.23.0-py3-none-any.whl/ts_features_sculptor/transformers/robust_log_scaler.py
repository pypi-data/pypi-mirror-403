import numpy as np
import pandas as pd
from typing import Callable, Optional
from dataclasses import dataclass, field
from sklearn.base import BaseEstimator, TransformerMixin


def _log1p_safe(x: pd.Series | np.ndarray) -> pd.Series:
    return np.log1p(x.astype(float))


def _expm1_safe(x: pd.Series | np.ndarray) -> pd.Series:
    return np.expm1(x.astype(float))


@dataclass
class RobustLogScaler(BaseEstimator, TransformerMixin):
    """
    Робастная медианная стандартизация на растущем окне

        z_i = 0.6745 · (f(x_i) − median_{≤i}) /
              (max(MAD_{≤i}, eps_val) + add_eps)

    где
        eps_val  = max(0.05·|median_{≤i}|, 1e-6) или заданный self.eps,
        add_eps  – фиксированная добавка к знаменателю (по умолчанию 1e‑6).

    Все параметры вычисляются **только** по индивидуальному ряду клиента.
    """

    # --- основные поля ----------------------------------------------------
    feature_col: str = "target"
    out_col: Optional[str] = None

    transform_func: Callable[[pd.Series | np.ndarray], pd.Series] = _log1p_safe
    inverse_func: Callable[[pd.Series | np.ndarray], pd.Series] = _expm1_safe

    eps: Optional[float] = None          # адаптивный порог MAD
    add_eps: float = 1e-6                # новое: добавка к знаменателю
    strategy_if_const: str = "eps"       # {"eps", "nan"}

    lookback: Optional[int] = None       # None -> expanding от начала
    keep_params: bool = True
    const_flag_col: Optional[str] = None

    # --- внутреннее хранение ----------------------------------------------
    _median_series_: Optional[np.ndarray] = field(init=False, default=None)
    _mad_series_: Optional[np.ndarray] = field(init=False, default=None)

    # --- вспомогательные методы -------------------------------------------
    def _compute_eps(self, med):
        """eps_val = max(0.05·|median|, 1e-6)  или self.eps."""
        if self.eps is not None:
            return self.eps
        med_arr = np.asarray(med, dtype=float)
        eps_val = 0.05 * np.abs(med_arr)
        return np.where(eps_val == 0, 1e-6, eps_val)

    # --- sklearn API -------------------------------------------------------
    def fit(self, X: pd.DataFrame, y=None):
        if self.feature_col not in X.columns:
            raise ValueError(f"RobustLogScaler: нет колонки '{self.feature_col}'")
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if self.feature_col not in X.columns:
            raise ValueError(f"RobustLogScaler: '{self.feature_col}' отсутствует")
        if self.strategy_if_const not in {"eps", "nan"}:
            raise ValueError("strategy_if_const ∈ {'eps','nan'}")

        df = X.copy()
        x_t = self.transform_func(df[self.feature_col])

        # скользящее или нарастающее окно
        if self.lookback:
            med = x_t.rolling(self.lookback, min_periods=1).median()
            mad = (x_t - med).abs().rolling(self.lookback, min_periods=1).median()
        else:
            med = x_t.expanding(min_periods=1).median()
            mad = (x_t - med).abs().expanding(min_periods=1).median()

        # устойчивый знаменатель
        eps_val = self._compute_eps(med)
        mad_clipped = np.maximum(mad, eps_val)
        if self.strategy_if_const == "nan":
            mad_clipped = mad_clipped.where(mad != 0, np.nan)

        denom = mad_clipped + self.add_eps        # <-- главное изменение
        z = 0.6745 * (x_t - med) / denom

        dst = self.out_col or self.feature_col
        df[dst] = z

        if self.keep_params:
            df[f"{dst}_median"] = med
            df[f"{dst}_mad"] = mad
        if self.const_flag_col:
            df[self.const_flag_col] = mad.eq(0)

        # сохраняем статистики для inverse
        self._median_series_ = med.values
        self._mad_series_ = mad.values
        return df

    def inverse_transform(self, z: np.ndarray | pd.Series) -> np.ndarray:
        if self._median_series_ is None or self._mad_series_ is None:
            raise RuntimeError("inverse_transform: сначала вызовите transform()")

        z_arr = np.asarray(z, dtype=float)
        if z_arr.shape[0] != len(self._median_series_):
            raise ValueError("inverse_transform: длина z не совпадает со статистиками")

        med = self._median_series_
        eps_val = self._compute_eps(med)
        mad = np.asarray(self._mad_series_, dtype=float)
        mad_clipped = np.maximum(mad, eps_val)
        denom = mad_clipped + self.add_eps   # тот же знаменатель

        raw = z_arr * denom / 0.6745 + med
        return self.inverse_func(raw)
