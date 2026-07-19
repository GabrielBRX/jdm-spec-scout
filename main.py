from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import sys
import asyncio

# 🛠️ CORREÇÃO PARA O PLAYWRIGHT RODAR NO WINDOWS COM UVICORN:
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

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


# 4. Rota para Disparar a Raspagem (Otimizada e Assíncrona Nativa)
@app.post("/api/scrape", tags=["Automação & Carga"])
async def disparar_e_salvar_raspagem(db: Session = Depends(get_db)):
    """
    Dispara o robô assíncrono Playwright usando o loop nativo do FastAPI,
    evitando conflitos de concorrência com o Uvicorn no Windows.
    """
    try:
        print("🔌 Rota /api/scrape acionada de forma assíncrona nativa!")
        print("🤖 Chamando o robô Playwright focado por Keywords...")
        
        # Como a rota agora é 'async def', podemos simplesmente usar await direto na função assíncrona!
        # Isso evita criar e fechar loops manualmente, o que quebrava o Uvicorn às vezes.
        await garimpar_carused_completo(db)
        
        return {
            "status": "Sucesso", 
            "detalhes": "O robô Playwright varreu os alvos JDM com base nos filtros inteligentes por URL!"
        }
        
    except Exception as e:
        import traceback
        print("❌ ERRO CRÍTICO NO ROBÔ:")
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500, 
            detail=f"Erro na execução do robô: {str(e)}"
        )