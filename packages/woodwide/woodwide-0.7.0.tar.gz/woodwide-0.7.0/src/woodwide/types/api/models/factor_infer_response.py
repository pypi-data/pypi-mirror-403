# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from ...._models import BaseModel

__all__ = ["FactorInferResponse", "Factor"]


class Factor(BaseModel):
    id: int

    description: str

    strength: float


class FactorInferResponse(BaseModel):
    """
    Response for factors models.
    Contains human-interpretable factors that explain the data.
    """

    factors: List[Factor]
