from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

# Configuração do Banco de Dados (SQLite para começar fácil)
DATABASE_URL = "sqlite:///./cars.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cria as tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="JDM Spec Scout")

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