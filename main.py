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

# 3. Rota de Carros (Consultando direto o SQLite com Filtros opcionais)
@app.get("/api/cars", response_model=List[schemas.CarListingResponse], tags=["Estoque JDM"])
def obter_carros(
    cambio: Optional[str] = None, 
    cor: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de todos os carros cadastrados no banco de dados.
    Permite filtrar opcionalmente por câmbio (Ex: 'Manual') ou por cor (Ex: 'White').
    """
    try:
        # Inicia a query consultando a tabela CarListing
        query = db.query(models.CarListing)
        
        # Se o usuário mandou o filtro de câmbio, aplica na query
        if cambio:
            query = query.filter(models.CarListing.cambio.ilike(f"%{cambio}%"))
            
        # Se o usuário mandou o filtro de cor, aplica na query
        if cor:
            query = query.filter(models.CarListing.cor.ilike(f"%{cor}%"))
            
        # Executa a query e traz os resultados
        carros_do_banco = query.all()
        
        return carros_do_banco
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno ao consultar o banco de dados: {str(e)}"
        )