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


# schemas.py
from pydantic import BaseModel

class CarListingResponse(BaseModel):
    id: int
    stock_id: str
    carro: str
    ano_mes: str
    preco: str
    quilometragem: str
    cambio: str
    cor: str
    localizacao: str
    fonte: str

    class Config:
        from_attributes = True  # Para o Pydantic ler direto do modelo do SQLAlchemy