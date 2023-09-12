from __future__ import annotations
from typing import List, Optional

from factors.base_factor import BaseFactor


class PerfFactor(BaseFactor):

    def __init__(self, name, comp_type, model):
        super().__init__(name, comp_type, model)

    @classmethod
    def get_prediction(cls, predictors: List[BaseFactor], name: str, comp_type: int, perf: float, **kwargs) -> Optional[float]:
        return super().get_prediction(predictors, name, comp_type, perf, cls)
