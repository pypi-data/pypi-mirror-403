from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


@dataclass
class HierarchicalAssignmentPolicyWeights(BaseEstimator, TransformerMixin):
    """
    Иерархическое смешивание двух календарных весов политики назначения.

    Полагаем, что в таблице X уже есть два веса:
      - coarse_weight (например, year x dow0 x hour_bucket)
      - fine_weight   (например, year x month x dow0 x hour_bucket)
    и опора для fine-уровня например, fine_support = days_cnt.

    Смешивание (partial pooling) делается в log-пространстве:

      s = n / (n + k)
      log(w_out) = (1 - s) * log(w_coarse) + s * log(w_fine)
      w_out = exp(log(w_out))

    где:
      - n = fine_support (exposure/support)
      - k = гиперпараметр "сила coarse" (псевдо-опора)

    Fallback по пропускам:
      - если нет fine_weight -> берём coarse_weight
      - если нет coarse_weight -> берём fine_weight
      - если нет обоих -> 1.0

    Parameters
    ----------
    fine_weight_col : str
        Колонка с fine_weight.
    fine_support_col : str
        Колонка с fine_support (n).
    coarse_weight_col : str
        Колонка с coarse_weight.
    k : float
        Псевдо-опора (n0). Чем больше k, тем сильнее тянем к coarse_weight.
    out_weight_col : str
        Имя выходной колонки.
    eps : float
        Нижняя отсечка для весов (нужна, чтобы log был определён).

    Examples
    --------
    >>> import pandas as pd
    >>> X = pd.DataFrame({
    ...   "w_y":  [0.5, 2.0, 1.0, np.nan],
    ...   "w_ym": [0.2, 3.0, np.nan, 1.5],
    ...   "n_ym": [10, 100, 10, 50],
    ... })
    >>> tr = HierarchicalAssignmentPolicyWeights(
    ...   fine_weight_col="w_ym",
    ...   fine_support_col="n_ym",
    ...   coarse_weight_col="w_y",
    ...   k=30.0,
    ...   out_weight_col="w",
    ... )
    >>> result_df = tr.fit_transform(X)
    >>> print(result_df.round(3).to_string(index=False))
     w_y  w_ym  n_ym     w
     0.5   0.2    10 0.398
     2.0   3.0   100 2.732
     1.0   NaN    10 1.000
     NaN   1.5    50 1.500
    """

    fine_weight_col: str
    fine_support_col: str
    coarse_weight_col: str
    k: float = 30.0
    out_weight_col: str = "scheduler_weight"
    eps: float = 1e-9

    def __post_init__(self):
        self.k = float(self.k)
        self.eps = float(self.eps)

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()

        w_f = pd.to_numeric(df[self.fine_weight_col], errors="coerce").to_numpy(
            dtype=float
        )
        w_c = pd.to_numeric(df[self.coarse_weight_col], errors="coerce").to_numpy(
            dtype=float
        )
        n = pd.to_numeric(df[self.fine_support_col], errors="coerce").to_numpy(
            dtype=float
        )

        out = np.full(len(df), np.nan, dtype=float)

        has_f = np.isfinite(w_f)
        has_c = np.isfinite(w_c)
        has_n = np.isfinite(n)

        both = has_f & has_c
        if both.any():
            n_eff = np.zeros_like(n, dtype=float)
            n_eff[both & has_n] = n[both & has_n]
            n_eff = np.clip(n_eff, 0.0, np.inf)

            s = n_eff[both] / (n_eff[both] + self.k)

            wf = np.clip(w_f[both], self.eps, np.inf)
            wc = np.clip(w_c[both], self.eps, np.inf)

            out[both] = np.exp((1.0 - s) * np.log(wc) + s * np.log(wf))

        only_c = has_c & ~has_f
        if only_c.any():
            out[only_c] = w_c[only_c]

        only_f = has_f & ~has_c
        if only_f.any():
            out[only_f] = w_f[only_f]

        none = ~has_f & ~has_c
        if none.any():
            out[none] = 1.0

        out = np.clip(out, self.eps, np.inf)
        df[self.out_weight_col] = out
        return df
