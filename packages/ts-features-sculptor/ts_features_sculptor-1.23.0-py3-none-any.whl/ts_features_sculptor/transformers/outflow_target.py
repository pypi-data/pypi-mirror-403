import pandas as pd
from dataclasses import dataclass
from sklearn.base import BaseEstimator, TransformerMixin


@dataclass
class OutflowTarget(BaseEstimator, TransformerMixin):
    """
    Трансформер для построения таргета «выбывание при превышении порога
    отсутствия» (outflow) на основе столбцов tte и разметки цензуры.

    Предполагается, что:
    - tte_col содержит длительность (в днях) до следующего визита или до
      конца наблюдений (правое цензурирование);
    - censor_flag_col = 1 означает отсутствие следующего визита в пределах
      данного tte (правое цензурирование по визиту);
    - порог tau_days задаёт временной порог отсутствия, после которого
      считаем, что объект «выбыл» из процесса.

    Определения
    -----------
    Для каждой строки:

    duration_outflow = min(tte, tau_days)

    outflow_event = 1, если:
        tte >= tau_days и censor_flag_col == 1
      (мы наблюдаем отсутствие не меньше tau_days и возврата нет);

    outflow_event = 0, иначе:
      - либо был возврат раньше порога (tte < tau_days и censor_flag_col == 0),
      - либо наблюдали отсутствие меньше порога и данные закончились
        (tte < tau_days и censor_flag_col == 1).

    Таким образом:
    - outflow_event=1 — наблюдаемое событие «выбыл относительно порога»;
    - outflow_event=0 — правая цензура для процесса outflow.

    Parameters
    ----------
    tte_col : str, default="tte"
        Название столбца с длительностями (в днях).
    censor_flag_col : str, default="is_censored"
        Название столбца с флагом цензурирования по визиту (0/1).
    tau_days : float, default=30.0
        Порог отсутствия (в днях), после которого считаем, что произошло
        событие outflow.
    duration_col : str, default="duration_outflow"
        Название выходного столбца с длительностью для outflow-процесса.
    event_col : str, default="event_outflow"
        Название выходного столбца с бинарным флагом события outflow.

    Examples
    --------
    >>> import pandas as pd
    >>> from ts_features_sculptor import OutflowTarget
    >>>
    >>> df = pd.DataFrame({
    ...     "tte": [9.0, 69.0, 5.0, 7.0],
    ...     "is_censored": [0, 1, 0, 1],
    ... })
    >>> tr = OutflowTarget(tau_days=30.0)
    >>> res = tr.fit_transform(df)
    >>> res[["tte", "duration_outflow", "event_outflow"]]
        tte  duration_outflow  event_outflow
    0   9.0               9.0              0
    1  69.0              30.0              1
    2   5.0               5.0              0
    3   7.0               7.0              0
    """

    tte_col: str = "tte"
    censor_flag_col: str = "is_censored"
    tau_days: float = 30.0
    duration_col: str = "duration_outflow"
    event_col: str = "event_outflow"

    def __post_init__(self) -> None:
        if self.tau_days <= 0:
            raise ValueError("OutflowTarget: tau_days должен быть > 0.")

    def fit(self, X: pd.DataFrame, y=None):
        # Здесь никаких статистик не накапливаем
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()

        if self.tte_col not in df.columns:
            raise ValueError(
                f"OutflowTarget: столбец '{self.tte_col}' отсутствует во входном DataFrame."
            )
        if self.censor_flag_col not in df.columns:
            raise ValueError(
                f"OutflowTarget: столбец '{self.censor_flag_col}' отсутствует во входном DataFrame."
            )

        tte = df[self.tte_col].astype("float64")
        is_censored = df[self.censor_flag_col].astype("bool")

        # Длительность для outflow-процесса: не больше порога
        duration = tte.clip(upper=self.tau_days)

        # Событие outflow: отсутствие >= tau и возврата нет (цензура по визиту)
        event = (tte >= self.tau_days) & is_censored

        df[self.duration_col] = duration.astype("float32")
        df[self.event_col] = event.astype("int8")

        return df
