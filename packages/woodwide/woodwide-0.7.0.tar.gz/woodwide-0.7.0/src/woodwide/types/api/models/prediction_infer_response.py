# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Union, Optional

from ...._models import BaseModel

__all__ = ["PredictionInferResponse"]


class PredictionInferResponse(BaseModel):
    """
    Response for prediction models.
    Contains 'prediction' mapping row IDs to predicted values.
    May contain 'prediction_prob' mapping row IDs to probabilities.
    """

    prediction: Dict[str, Union[float, str]]

    prediction_prob: Optional[Dict[str, float]] = None
