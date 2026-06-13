from pydantic import BaseModel
from typing import Optional


class CarListingBase(BaseModel):
    stock_id: str
    carro: str
    ano_mes: str
    preco: str
    quilometragem: str
    cambio: str
    cor: str
    localizacao: str
    fonte: Optional[str] = "SBT Japan"

class CarListingCreate(CarListingBase):
    pass


class CarListingResponse(CarListingBase):
    id: int

    class Config:
        from_attributes = True