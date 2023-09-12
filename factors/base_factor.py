from __future__ import annotations
from typing import List, Optional


class BaseFactor:

    def __init__(self, name, comp_type, model):
        self.name: str = name
        self.comp_type: int = comp_type  # Category
        self.model = model

    def __call__(self, *args, **kwargs):
        return self.model(*args, **kwargs)

    @classmethod
    def get_prediction(cls, predictors: List[BaseFactor], name: str, comp_type: int, perf: float, type_) -> Optional[float]:
        for predictor in predictors:
            if predictor.name == name and predictor.comp_type == comp_type and isinstance(predictor, type_):
                return predictor(perf)
        return None
