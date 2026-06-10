import json
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import models
import schemas

# 1. Configuração do Banco de Dados SQLite
DATABASE_URL = "sqlite:///./cars.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cria as tabelas no banco de dados se não existirem
models.Base.metadata.create_all(bind=engine)

# 2. Inicialização do FastAPI
app = FastAPI(title="JDM Spec Scout")

# Configuração do caminho do JSON na pasta data
BASE_DIR = Path(__file__).resolve().parent
JSON_DATA_PATH = BASE_DIR / "data" / "carros_estoque_limpo.json"

# Dependência do Banco de Dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rota Inicial
@app.get("/", tags=["Geral"])
def rota_inicial():
    return {
        "status": "Online",
        "projeto": "JDM Spec Scout",
        "documentacao": "/docs"
    }

# 3. Rota do SBT Japan
@app.get("/api/cars/sbt", tags=["Scrapers"])
def obter_carros_sbt():
    """
    Retorna a lista de carros importados e higienizados do SBT Japan.
    """
    if not JSON_DATA_PATH.exists():
        raise HTTPException(
            status_code=404, 
            detail="Arquivo de estoque limpo não encontrado. Certifique-se de rodar o script de limpeza primeiro."
        )
    
    try:
        with open(JSON_DATA_PATH, "r", encoding="utf-8") as f:
            dados_carros = json.load(f)
        return dados_carros
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno ao ler os dados do estoque: {str(e)}"
        )