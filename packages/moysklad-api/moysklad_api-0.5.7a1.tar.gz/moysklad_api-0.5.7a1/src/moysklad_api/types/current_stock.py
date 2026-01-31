from pydantic import BaseModel, Field


class CurrentStock(BaseModel):
    assortment_id: str = Field(..., alias="assortmentId")
    stock: float = Field(..., alias="stock")
