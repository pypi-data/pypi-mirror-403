# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List

from ...._models import BaseModel

__all__ = ["EmbeddingInferResponse"]


class EmbeddingInferResponse(BaseModel):
    """
    Response for embedding models.
    'embeddings' key contains a map of row indices to their vector embeddings.
    """

    embeddings: Dict[str, List[float]]
