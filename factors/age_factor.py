from __future__ import annotations
from typing import List, Optional, Union

import numpy as np
from scipy.optimize import curve_fit

from factors.base_factor import BaseFactor
from global_vars import ReferenceValue


class AgeModel:
    def __init__(self, x, y):
        params, _ = curve_fit(self.fit_func, x, y)
        self.a = params[0]
        self.b = params[1]
        self.c = params[2]

    def __call__(self, x) -> Union[float, List[float]]:
        if isinstance(x, list) or isinstance(x, List) or isinstance(x, np.ndarray):
            return [1 / x for x in self.fit_func(x, self.a, self.b, self.c)]
        return 1 / self.fit_func(x, self.a, self.b, self.c)

    def fit_func(self, x, a, b, c) -> Union[float, List[float]]:
        if isinstance(x, list) or isinstance(x, List) or isinstance(x, np.ndarray):
            return [a * x1 ** 2 + b * x1 + c if x1 != -1 else 1 / ReferenceValue.GPU_FACTOR for x1 in x]
        return a * x ** 2 + b * x + c if x != -1 else 1 / ReferenceValue.GPU_FACTOR


class AgeFactor(BaseFactor):

    def __init__(self, name, comp_type, model):
        super().__init__(name, comp_type, model)
        self.model: AgeModel = self.model

    @classmethod
    def get_prediction(cls, predictors: List[BaseFactor], name: str, comp_type: int, perf: float, **kwargs) -> Optional[float]:
        return super().get_prediction(predictors, name, comp_type, perf, cls)
