from pydantic import BaseModel, Field
from typing import Optional, List

class Recommendation(BaseModel):
    product_id: str
    current_price: float
    recommended_price: float
    unit_cost: float
    competitor_median_price: Optional[float] = None
    inventory_on_hand: Optional[int] = None
    reorder_point: Optional[int] = None
    expected_profit_delta: float
    notes: str

class RecommendResponse(BaseModel):
    recommendations: List[Recommendation]
    saved_csv_path: Optional[str] = None
    message: str = Field(default="ok")

class Health(BaseModel):
    status: str = "ok"