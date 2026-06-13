import json
import sys
from pathlib import Path  

caminho_atual = Path(__file__).resolve().parent
raiz_projeto = caminho_atual.parent
sys.path.append(str(raiz_projeto))

from database import SessionLocal
from models import CarListing, Base
from database import engine

def popular_banco_de_dados():
    print("🗄️ [jdm-spec-scout]: Iniciando a carga de dados no SQLite...")

    Base.metadata.create_all(bind=engine)

    caminho_json = raiz_projeto / "data" / "carros_estoque_limpo.json"

    if not caminho_json.exists():
        print(f"❌ Erro: O arquivo {caminho_json} não foi encontrado!")
        print("Rode o script 'limpar_dados.py' primeiro.")
        return
    
    db = SessionLocal()

    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            carros = json.load(f)
        
        
        contador_novos = 0
        contador_existentes = 0
        
        for c in carros:
           

            carro_existente = db.query(CarListing).filter(CarListing.stock_id == c["stock_id"]).first()

            if not carro_existente:
                novo_carro = CarListing(
                    stock_id=c["stock_id"],
                    carro=c["carro"],
                    ano_mes=c["ano_mes"],
                    preco=c["preco"],
                    quilometragem=c["quilometragem"],
                    cambio=c["cambio"],
                    cor=c["cor"],
                    localizacao=c["localizacao"],
                    fonte="SBT Japan" 
                )
                db.add(novo_carro)
                contador_novos += 1
            else:
                contador_existentes += 1
        
        db.commit()
        print(f"✨ Sucesso! Banco atualizado.")
        print(f"📥 Novos carros inseridos: {contador_novos}")
        print(f"🔄 Carros já existentes pulados: {contador_existentes}")

    except Exception as e:
        db.rollback()
        print(f"❌ Ocorreu um erro ao salvar no banco: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    popular_banco_de_dados()
