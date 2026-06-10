from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
import schemas
import httpx

from fastapi import Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from fastapi import HTTPException

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

@app.get("/cars/check-url/", response_model=schemas.Car)
def get_car_by_url(url: str, db: Session = Depends(get_db)):
    car = db.query(models.carlisting).filter(models.carlisting.url == url).first()
    if not car:
        raise HTTPException(status_code=404, detail="Carro não encontrado com esta URL")
    return car

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
async def create_car(car: schemas.CarCreate, db: Session = Depends(get_db)):

    url_api = "https://economia.awesomeapi.com.br/json/last/JPY-BRL,JPY-USD"

    try:

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url_api)
            response.raise_for_status()
            dados_moeda = response.json()

        taxa_brl = float(dados_moeda["JPYBRL"]["bid"])
        taxa_usd = float(dados_moeda["JPYUSD"]["bid"])
    
    except (httpx.HTTPError, KeyError, IndexError):
        taxa_brl = 0.035
        taxa_usd = 0.0063

    convertido_brl = car.price_jpy * taxa_brl
    convertido_usd = car.price_jpy * taxa_usd


    new_car = models.carlisting(
        model=car.model,
        auction_grade=car.auction_grade,
        mileage=car.mileage,
        price_jpy=car.price_jpy,
        price_brl=convertido_brl,
        price_usd=convertido_usd,
        transmission=car.transmission,
        url=car.url
    )

    db.add(new_car)
    db.commit()
    db.refresh(new_car)
    return new_car

@app.get("/cars/", response_model=List[schemas.Car])
def read_cars(
    max_mileage: Optional[int] = None,
    transmission: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.carlisting)

    if max_mileage is not None:
        query = query.filter(models.carlisting.mileage <= max_mileage)

    if transmission is not None:
        query = query.filter(models.carlisting.transmission.ilike(f"%{transmission}%"))

    cars = query.all()
    return cars

@app.put("/cars/{car_id}", response_model=schemas.Car)
async def update_car(car_id: int, car_update: schemas.CarCreate, db: Session = Depends(get_db)):
    db_car = db.query(models.carlisting).filter(models.carlisting.id == car_id).first()
    if not db_car:
        raise HTTPException(status_code=404, detail="Carro não encontrado")
    
    url_api = "https://economia.awesomeapi.com.br/json/last/JPY-BRL,JPY-USD"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url_api)
            response.raise_for_status()
            dados_moeda = response.json()

        taxa_brl = float(dados_moeda["JPYBRL"]["bid"])
        taxa_usd = float(dados_moeda["JPYUSD"]["bid"])
    except (httpx.HTTPError, KeyError, IndexError):
        taxa_brl = 0.035
        taxa_usd = 0.0063

    convertido_brl = car_update.price_jpy * taxa_brl
    convertido_usd = car_update.price_jpy * taxa_usd

    db_car.model = car_update.model
    db_car.auction_grade = car_update.auction_grade
    db_car.mileage = car_update.mileage
    db_car.price_jpy = car_update.price_jpy
    db_car.price_brl = convertido_brl
    db_car.price_usd = convertido_usd
    db_car.transmission = car_update.transmission
    db_car.url = car_update.url

    db.commit()
    db.refresh(db_car)
    return db_car
   
@app.delete("/cars/{car_id}")
def delete_car(car_id: int, db: Session = Depends(get_db)):
    db_car = db.query(models. carlisting).filter(models.carlisting.id == car_id).first()

    if not db_car:
        raise HTTPException(status_code=404, detail="Carro não encontrado no banco de dados")
    
    db.delete(db_car)
    db.commit()
    return {"message": f"Sucesso! O veículo ID {car_id} ({db_car.model}) foi removido."}

