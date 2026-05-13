from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
import schemas

from fastapi import Depends
from sqlalchemy.orm import Session
from typing import List


# Configuração do Banco de Dados (SQLite para começar fácil)
DATABASE_URL = "sqlite:///./cars.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cria as tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="JDM Spec Scout")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return{
        "status": "Online",
        "message": "Searching for the perferct FD3S...",
        "goal": "Grade 4 RX-7"
    }

@app.get("/check-cars")
def check_cars():

    # Por enquanto retorna uma lista vazia, mas confirma que a rota funciona
    return {"listings": []}

@app.post("/cars/", response_model=schemas.Car)
def create_car(car: schemas.CarCreate, db: Session = Depends(get_db)):

    exchange_rate = 0.034
    converted_price = car.price_jpy * exchange_rate

    new_car = models.carlisting(
        model=car.model,
        auction_grade=car.auction_grade,
        mileage=car.mileage,
        price_jpy=car.price_jpy,
        price_brl=converted_price,
        transmission=car.transmission,
        url=car.url
    )

    db.add(new_car)
    db.commit()
    db.refresh(new_car)
    return new_car

@app.get("/cars/", response_model=List[schemas.Car])
def read_cars(db: Session = Depends(get_db)):
    cars = db.query(models.carlisting).all()
    return cars






