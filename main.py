import sys
import asyncio

# 🛠️ FORÇAR O PROACTOR EVENT LOOP NO WINDOWS (DEVE SER A PRIMEIRA COISA)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from notifier import verificar_e_notificar

from scrapers.carused_scraper import garimpar_carused_completo
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

# 3. Rota de Carros (Consultando direto o SQLite com Filtros Dinâmicos)
@app.get("/api/cars", response_model=List[schemas.CarListingResponse], tags=["Estoque JDM"])
def obter_carros(
    carro: Optional[str] = None,
    cambio: Optional[str] = None, 
    cor: Optional[str] = None,
    localizacao: Optional[str] = None,
    fonte: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de todos os carros cadastrados no banco de dados.
    Permite filtrar dinamicamente por modelo/marca, câmbio, cor, localização ou fonte.
    """
    try:
        query = db.query(models.CarListing)
        
        if carro:
            query = query.filter(models.CarListing.carro.ilike(f"%{carro}%"))
        if cambio:
            query = query.filter(models.CarListing.cambio.ilike(f"%{cambio}%"))
        if cor:
            query = query.filter(models.CarListing.cor.ilike(f"%{cor}%"))
        if localizacao:
            query = query.filter(models.CarListing.localizacao.ilike(f"%{localizacao}%"))
        if fonte:
            query = query.filter(models.CarListing.fonte.ilike(f"%{fonte}%"))
            
        return query.all()
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno ao consultar o banco de dados: {str(e)}"
        )


import concurrent.futures

executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

@app.post("/api/scrape", tags=["Automação & Carga"])
async def disparar_e_salvar_raspagem(db: Session = Depends(get_db)):
    """
    Dispara o robô isolando-o em uma thread separada, 
    eliminando o conflito de loop do Windows com o Playwright.
    """
    try:
        print("🔌 Rota /api/scrape acionada!")
        
        loop = asyncio.get_running_loop()
        
        
        await loop.run_in_executor(
            executor, 
            lambda: asyncio.run(garimpar_carused_completo(db))
        )
        
        
        print("📱 [JDM-SCOUT]: Disparando alertas para o Telegram...")
        await verificar_e_notificar()
        
        return {
            "status": "Sucesso", 
            "detalhes": "Robô executado com sucesso em thread isolada e alertas enviados!"
        }
        
    except Exception as e:
        import traceback
        print("❌ ERRO CRÍTICO NO ROBÔ:")
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500, 
            detail=f"Erro na execução do robô: {str(e)}"
        )