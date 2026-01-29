from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


@dataclass
class CalendarAssignmentPolicyStats(BaseEstimator, TransformerMixin):
    """
    Трансформер для применения календарной политики назначения
    воздействия по внешнему глобальному профилю.

    По таблице профиля (base_profile_df) строит:
      - scheduler_intensity(keys) = (push_cnt + alpha) / (days_cnt + beta)
      - scheduler_weight(keys) = scheduler_intensity
        / mean(scheduler_intensity | normalize_keys)
      - support_cnt(keys) = days_cnt

    Parameters
    ----------
    base_profile_df : pd.DataFrame
    keys : tuple[str, ...]
        Ключи для lookup, например ("year", "dow0", "hour_bucket_12")
    push_cnt_col, days_cnt_col : str
        Сырые счётчики назначения воздействия и экспозиция (календарные
        дни).
    alpha, beta : float | None
        Коэффициенты сглаживания:
          scheduler_intensity = (push_cnt + alpha) / (days_cnt + beta)
        Если alpha или beta равны None, они оцениваются эмпирически
        (см. estimate_poisson_gamma_prior).
    estimate_prior_method : str
        "kappa" | "moments" выбор метода метода оценки (alpha, beta).
    kappa : float
        Псевдо-экспозиция для метода "kappa".
    min_days : float
        Минимальная экспозиция для метода "moments".
    normalize_keys : tuple[str, ...] | None
        Ключи нормировки веса:
          scheduler_weight = scheduler_intensity
            / mean(scheduler_intensity | normalize_keys).
        Если None, нормируем на глобальное среднее по профилю.
    fillna : str | None
        "mean" | "const" | None.
        Что делать, если ключей нет в профиле.
    fillna_value : float
        Значение для fillna="const".
    out_intensity_col, out_weight_col, out_support_col : str
        Имена выходных колонок.
    eps : float
        Нижняя отсечка для scheduler_weight.

    Examples
    --------
    >>> import pandas as pd
    >>> base_profile_df = pd.DataFrame({
    ...   "year": [2021, 2021, 2021, 2021],
    ...   "dow0": [0, 1, 0, 1],      # 0=Пн, 1=Вт
    ...   "hour_bucket": [0, 0, 12, 12],
    ...   "hist_push_cnt": [2, 12, 10, 4],
    ...   "hist_days": [52, 52, 52, 52],
    ... })
    >>>
    >>> X = pd.DataFrame({
    ...   "time": pd.to_datetime([
    ...     "2021-01-04",  # Пн
    ...     "2021-01-05",  # Вт
    ...     "2021-01-06",  # Ср работает fillna
    ...   ]),
    ...   "year": [2021, 2021, 2021],
    ...   "dow0": [0, 1, 2],
    ...   "hour_bucket": [0, 0, 0],
    ... })
    >>>
    >>> tr = CalendarAssignmentPolicyStats(
    ...   base_profile_df=base_profile_df,
    ...   keys=("year", "dow0", "hour_bucket"),
    ...   push_cnt_col="hist_push_cnt",
    ...   days_cnt_col="hist_days",
    ...   # alpha=1,
    ...   # beta=1,
    ...   normalize_keys=("year",),
    ...   fillna="mean",
    ...   out_intensity_col="scheduler_intensity",
    ...   out_weight_col="scheduler_weight",
    ...   out_support_col="support_cnt",
    ... )
    >>> result_df = tr.fit_transform(X)
    >>> print(result_df.round(2).to_string(index=False))
          time  year  dow0  hour_bucket  scheduler_intensity  scheduler_weight  support_cnt
    2021-01-04  2021     0            0                 0.06              0.38         52.0
    2021-01-05  2021     1            0                 0.25              1.62         52.0
    2021-01-06  2021     2            0                 0.15              1.00         52.0
    """

    base_profile_df: pd.DataFrame
    keys: tuple[str, ...]
    push_cnt_col: str = "hist_push_cnt"
    days_cnt_col: str = "hist_days"
    alpha: float | None = None
    beta: float | None = None
    estimate_prior_method: str = "kappa"
    kappa: float = 30.0
    min_days: float = 7.0
    normalize_keys: tuple[str, ...] | None = None
    fillna: str | None = "mean"
    fillna_value: float = 1.0
    out_intensity_col: str = "scheduler_intensity"
    out_weight_col: str = "scheduler_weight"
    out_support_col: str = "support_cnt"
    eps: float = 1e-9

    def __post_init__(self):
        self.keys = tuple(self.keys)
        self.normalize_keys = (
            tuple(self.normalize_keys)
            if self.normalize_keys is not None
            else None
        )
        self.alpha = None if self.alpha is None else float(self.alpha)
        self.beta = None if self.beta is None else float(self.beta)
        self.kappa = float(self.kappa)
        self.min_days = float(self.min_days)
        self.fillna_value = float(self.fillna_value)
        self.eps = float(self.eps)

    @staticmethod
    def estimate_poisson_gamma_prior(
        push: pd.Series,
        days: pd.Series,
        method: str = "kappa",
        kappa: float = 30.0,
        min_days: float = 7.0,
    ) -> tuple[float, float]:
        """
        Оценка априора Gamma(alpha, beta) для интенсивности lambda
        в модели Poisson-Gamma:
          treat_cnt ~ Poisson(lambda * exposure)
          lambda ~ Gamma(shape=alpha, rate=beta)

        Возвращает (alpha, beta) в параметризации (shape, rate):
          E[lambda] = alpha / beta.

        method="kappa":
          mu = sum(treat_cnt) / sum(exposure)
          beta = kappa
          alpha = mu * kappa

        method="moments" (эмпирический Байес по моментам):
          r = treat_cnt / exposure
          Var(r) ~= mu/exposure + mu^2/alpha
          => alpha ~= mu^2 / E[(r - mu)^2 - mu/exposure]
        """
        push = pd.to_numeric(push, errors="coerce").astype(float)
        days = pd.to_numeric(days, errors="coerce").astype(float)

        tot_days = float(np.nansum(days.to_numpy(dtype=float)))
        if tot_days <= 0.0:
            return 1.0, 1.0

        mu = float(np.nansum(push.to_numpy(dtype=float)) / tot_days)

        if method == "kappa":
            beta = float(kappa)
            alpha = float(mu * beta)
            return alpha, beta

        if method != "moments":
            raise ValueError('method must be "kappa" or "moments"')

        r = (push / days).to_numpy(dtype=float)
        e = days.to_numpy(dtype=float)

        mask = np.isfinite(r) & np.isfinite(e) & (e >= float(min_days))
        if mask.sum() == 0:
            beta = float(kappa)
            alpha = float(mu * beta)
            return alpha, beta

        adj = (r[mask] - mu) ** 2 - (mu / e[mask])
        adj = np.clip(adj, 0.0, np.inf)

        s2 = float(np.average(adj, weights=e[mask])) if adj.size else 0.0
        if s2 <= 0.0:
            beta = float(kappa)
            alpha = float(mu * beta)
            return alpha, beta

        alpha = float((mu * mu) / s2)
        beta = float(alpha / mu) if mu > 0.0 else float(kappa)
        print(f'{alpha=}, {beta=}')
        return alpha, beta

    def fit(self, X: pd.DataFrame, y=None):
        prof = self.base_profile_df

        self._key_dtypes = {k: prof[k].dtype for k in self.keys}

        push = pd.to_numeric(prof[self.push_cnt_col], errors="coerce") \
            .astype(float)
        days = pd.to_numeric(prof[self.days_cnt_col], errors="coerce") \
            .astype(float)

        if self.alpha is None or self.beta is None:
            alpha, beta = self.estimate_poisson_gamma_prior(
                push=push,
                days=days,
                method=self.estimate_prior_method,
                kappa=self.kappa,
                min_days=self.min_days,
            )
            self.alpha_ = float(alpha)
            self.beta_ = float(beta)
        else:
            self.alpha_ = float(self.alpha)
            self.beta_ = float(self.beta)

        p = prof[list(self.keys)].copy()
        p["_push"] = push
        p["_days"] = days

        p = p.groupby(list(self.keys), as_index=False)[["_push", "_days"]].sum()

        intensity = (p["_push"] + self.alpha_) / (p["_days"] + self.beta_)
        support = p["_days"].to_numpy(dtype=float)

        if self.normalize_keys is None:
            denom = float(np.nanmean(intensity.to_numpy(dtype=float)))
            denom_arr = np.full(len(p), denom, dtype=float)
        else:
            denom_df = (
                pd.DataFrame({"_int": intensity})
                .join(p[list(self.normalize_keys)])
                .groupby(list(self.normalize_keys), as_index=False)["_int"]
                .mean()
                .rename(columns={"_int": "_denom"})
            )
            denom_arr = (
                p[list(self.normalize_keys)]
                .merge(
                    denom_df,
                    on=list(self.normalize_keys), how="left"
                )["_denom"].to_numpy(dtype=float)
            )

        weight = intensity.to_numpy(dtype=float) / denom_arr
        weight = np.clip(weight, self.eps, np.inf)

        idx = pd.MultiIndex.from_frame(p[list(self.keys)])
        self._intensity = pd.Series(intensity.to_numpy(dtype=float), index=idx)
        self._weight = pd.Series(weight, index=idx)
        self._support = pd.Series(support, index=idx)

        self._intensity_mean = float(
            np.nanmean(intensity.to_numpy(dtype=float)))
        self._weight_mean = float(np.nanmean(weight))
        self._support_mean = float(np.nanmean(support))
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()

        for k in self.keys:
            expected = self._key_dtypes[k]
            if df[k].dtype != expected:
                df[k] = df[k].astype(expected)

        idx = pd.MultiIndex.from_frame(df[list(self.keys)])

        intensity = self._intensity.reindex(idx).to_numpy(dtype=float)
        weight = self._weight.reindex(idx).to_numpy(dtype=float)
        support = self._support.reindex(idx).to_numpy(dtype=float)

        if self.fillna == "mean":
            mi = np.isnan(intensity)
            mw = np.isnan(weight)
            ms = np.isnan(support)
            if mi.any():
                intensity[mi] = self._intensity_mean
            if mw.any():
                weight[mw] = self._weight_mean
            if ms.any():
                support[ms] = self._support_mean
        elif self.fillna == "const":
            mi = np.isnan(intensity)
            mw = np.isnan(weight)
            ms = np.isnan(support)
            if mi.any():
                intensity[mi] = self.fillna_value
            if mw.any():
                weight[mw] = self.fillna_value
            if ms.any():
                support[ms] = self.fillna_value

        weight = np.clip(weight, self.eps, np.inf)

        df[self.out_intensity_col] = intensity
        df[self.out_weight_col] = weight
        df[self.out_support_col] = support
        return df


CalendarSchedulerStats = CalendarAssignmentPolicyStats
