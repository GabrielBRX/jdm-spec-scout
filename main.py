import sys
import asyncio
import concurrent.futures

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from notifier import verificar_e_notificar

# Importação dos scrapers
from scrapers.sbtjapan_scraper import raspar_sbt_japan
from scrapers.carused_scraper import garimpar_carused_completo
import models
import schemas

DATABASE_URL = "sqlite:///./cars.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(bind=engine)

# 👉 O 'app' DEVE SER CRIADO AQUI ANTES DAS ROTAS (@app.get / @app.post)
app = FastAPI(title="JDM Spec Scout")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", tags=["Geral"])
def rota_inicial():
    return {
        "status": "Online",
        "projeto": "JDM Spec Scout",
        "documentacao": "/docs"
    }


@app.get("/api/cars", response_model=List[schemas.CarListingResponse], tags=["Estoque JDM"])
def obter_carros(
    carro: Optional[str] = None,
    cambio: Optional[str] = None, 
    cor: Optional[str] = None,
    localizacao: Optional[str] = None,
    fonte: Optional[str] = None,
    db: Session = Depends(get_db)
):
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


executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

@app.post("/api/scrape", tags=["Automação & Carga"])
async def disparar_e_salvar_raspagem(db: Session = Depends(get_db)):
    """
    Executa em sequência a varredura na SBT Japan e no CarUsed, 
    salva tudo no banco unificado e envia os alertas para o Telegram.
    """
    try:
        print("🔌 Rota /api/scrape acionada (Varredura Completa)...")
        loop = asyncio.get_running_loop()
        
        def rodar_ambos_scrapers():
            print("🇯🇵 [1/2] Iniciando raspagem da SBT Japan...")
            try:
                raspar_sbt_japan()
                print("✅ SBT Japan finalizada com sucesso.")
            except Exception as e:
                print(f"❌ Erro na SBT Japan: {e}")

            print("🚗 [2/2] Iniciando raspagem do CarUsed...")
            try:
                asyncio.run(garimpar_carused_completo(db))
                print("✅ CarUsed finalizado com sucesso.")
            except Exception as e:
                print(f"❌ Erro no CarUsed: {e}")

        await loop.run_in_executor(
            executor, 
            rodar_ambos_scrapers
        )
        
        print("📱 [JDM-SCOUT]: Verificando novidades e disparando alertas para o Telegram...")
        await verificar_e_notificar()
        
        return {
            "status": "Sucesso", 
            "detalhes": "Varredura completa da SBT Japan e CarUsed realizada, dados salvos e Telegram notificado!"
        }
        
    except Exception as e:
        import traceback
        print("❌ ERRO CRÍTICO NO PROCESSO DE RASPAGEM:")
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500, 
            detail=f"Erro na execução dos robôs: {str(e)}"
        )