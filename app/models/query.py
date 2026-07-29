from pydantic import BaseModel

class QueryEmbedding(BaseModel):
    dense: list[float]
    sparse_indices: list[int]
    sparse_values: list[float]