from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class carlisting(Base):
    __tablename__ = "car_listings"

    id = Column (Integer, primary_key=True, index=True)
    model = Column(String)         # Ex: Mazda RX-7 FD3S
    auction_grade = Column(String) # Ex: 4, 3.5, R
    mileage = Column(Integer)      # Quilometragem
    price_jpy = Column(Float)      # Preço em Ienes
    price_brl = Column(Float)      # Preço em Reais
    price_usd = Column(Float)      # Preço em Dólares
    transmission = Column(String)  # Manual ou Automatic
    url = Column(String)           # Link do anúncio
