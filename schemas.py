from pydantic import BaseModel
from typing import Optional

class CarCreate(BaseModel):
    model: str
    auction_grade: str
    mileage: int
    price_jpy: float
    transmission: str
    url: Optional[str] = None

class Car(CarCreate):
    id: int
    price_brl: float
    price_usd: float

    class Config:
        from_attributes = True