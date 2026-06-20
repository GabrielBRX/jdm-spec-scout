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
        # Inicia a query consultando a tabela CarListing
        query = db.query(models.CarListing)
        
        # Filtro por Nome/Modelo do Carro (Ex: 'Mazda', 'RX-7')
        if carro:
            query = query.filter(models.CarListing.carro.ilike(f"%{carro}%"))

        # Filtro por Câmbio (Ex: 'Manual')
        if cambio:
            query = query.filter(models.CarListing.cambio.ilike(f"%{cambio}%"))
            
        # Filtro por Cor (Ex: 'White')
        if cor:
            query = query.filter(models.CarListing.cor.ilike(f"%{cor}%"))
            
        # Filtro por Localização (Ex: 'Osaka', 'Saitama')
        if localizacao:
            query = query.filter(models.CarListing.localizacao.ilike(f"%{localizacao}%"))
            
        # Filtro por Fonte de Origem (Ex: 'SBT Japan')
        if fonte:
            query = query.filter(models.CarListing.fonte.ilike(f"%{fonte}%"))
            
        # Executa a query com todos os filtros aplicados e traz os resultados
        carros_do_banco = query.all()
        
        return carros_do_banco
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno ao consultar o banco de dados: {str(e)}"
        )


# 4. Rota para Disparar a Raspagem e Alimentar o Banco de Dados
@app.post("/api/scrape", tags=["Automação & Carga"])
def disparar_e_salvar_raspagem(db: Session = Depends(get_db)):
    """
    Dispara o robô assíncrono Playwright para varrer o carused.jp
    e atualizar o banco de dados SQLite em tempo real.
    Garante o ProactorEventLoop correto no Windows para evitar o NotImplementedError.
    """
    try:
        print("🔌 Rota /api/scrape acionada! Configurando ambiente seguro para o Playwright...")
        
        # Criamos explicitamente um novo loop de eventos limpo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # No Windows, forçamos o ProactorEventLoop diretamente neste laço isolado
        if sys.platform == 'win32':
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
            
        print("🤖 Chamando o robô Playwright...")
        # Executa a função assíncrona dentro do laço configurado de forma síncrona para a rota
        loop.run_until_complete(garimpar_carused_completo(db))
        loop.close()
        
        return {
            "status": "Sucesso", 
            "detalhes": "O robô Playwright varreu as páginas JDM com sucesso e atualizou o seu SQLite!"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro na execução do robô: {str(e)}"
        )