from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


@dataclass
class Ratio(BaseEstimator, TransformerMixin):
    """
    Безопасное отношение двух колонок.

    out_col = numerator_col / denominator_col

    Parameters
    ----------
    numerator_col : str
        Имя числителя.
    denominator_col : str
        Имя знаменателя.
    out_col : str, default="ratio"
        Имя выходной колонки.
    fillna_value : float | None, default=0.0
        Значение для NaN в результате. Если None, NaN остаются.

    Notes
    -----
    Деление на 0 даёт NaN. Если задано fillna_value, то замещаем NaN.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({"a": [1.0, 2.0], "b": [2.0, 0.0]})
    >>> tr = Ratio("a", "b", out_col="a_over_b", fillna_value=0.0)
    >>> result_df = tr.transform(df)
    >>> print(result_df.to_string(index=False))
      a   b  a_over_b
    1.0 2.0       0.5
    2.0 0.0       0.0
    """
    numerator_col: str
    denominator_col: str
    out_col: str = "ratio"
    fillna_value: Optional[float] = 0.0

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if self.numerator_col not in X.columns:
            raise ValueError(
                f"Ratio: missing column {self.numerator_col!r}"
            )
        if self.denominator_col not in X.columns:
            raise ValueError(
                f"Ratio: missing column {self.denominator_col!r}"
            )

        df = X.copy()
        num = pd.to_numeric(
            df[self.numerator_col], errors="coerce"
        ).astype(float)
        den = pd.to_numeric(
            df[self.denominator_col], errors="coerce"
        ).astype(float)
        den = den.replace(0.0, np.nan)

        out = num / den
        out = out.replace([np.inf, -np.inf], np.nan)
        if self.fillna_value is not None:
            out = out.fillna(float(self.fillna_value))
        df[self.out_col] = out
        return df
