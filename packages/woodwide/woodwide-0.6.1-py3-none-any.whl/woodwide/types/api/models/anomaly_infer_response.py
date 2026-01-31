# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from ...._models import BaseModel

__all__ = ["AnomalyInferResponse"]


class AnomalyInferResponse(BaseModel):
    """
    Response for anomaly detection models.
    Returns a list of IDs (indices) from the input dataset identified as anomalous.
    """

    anomalous_ids: List[str]
