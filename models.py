from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CarListing(Base):
    __tablename__ = "car_listings"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String, unique=True, index=True) # ID único do estoque (Evita duplicados!)
    carro = Column(String)                             # Ex: Mazda RX-7
    ano_mes = Column(String)                           # Ex: 2002/1
    preco = Column(String)                             # Guardado como String "USD 31,910" para facilitar
    quilometragem = Column(String)                     # Guardado como "109,700km"
    cambio = Column(String)                            # Manual (MT) ou Automático (AT)
    cor = Column(String)                               # Ex: White, Red, Blue
    localizacao = Column(String)                       # Ex: Aichi, JAPAN
    fonte = Column(String, default="SBT Japan")
