import asyncio
import re
from playwright.async_api import async_playwright
import sys
import os
from sqlalchemy.orm import Session

# Garante que o Python ache o main e database na pasta pai
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models

async def garimpar_carused_completo(db: Session):
    print("🤖 [jdm-spec-scout]: Iniciando Varredura Avançada com Paginação na Carused...")
    
    FONTES_MARCAS = {
        "mazda": "https://carused.jp/pt/car-list/mazda",
        "toyota": "https://carused.jp/pt/car-list/toyota",
        "nissan": "https://carused.jp/pt/car-list/nissan",
        "mitsubishi": "https://carused.jp/pt/car-list/mitsubishi",
        "subaru": "https://carused.jp/pt/car-list/subaru"
    }
    
    # Lista estrita de lendas JDM para evitar falsos positivos
    ALVOS_ESTRITOS = [
        "rx-7", "rx7", "rx-8", "rx8", "miata", "roadster",
        "supra", "ae86", "chaser", "mr2", "celica", "altezza", "gt86", "gt-86", "86", "zn6", "a90",
        "skyline", "gt-r", "gtr", "r35", "silvia", "180sx", "240sx", "fairlady", "350z", "370z", "400z", "300zx",
        "impreza", "wrx", "sti", "legacy b4", "brz", "zd8",
        "lancer", "evolution", "evo", "3000gt", "gto", "fto"
    ]
    
    PAGINAS_POR_MARCA = 3  # Quantas páginas você quer varrer por marca?

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        total_novos_carros = 0
        
        try:
            for marca, url_base in FONTES_MARCAS.items():
                for pag in range(1, PAGINAS_POR_MARCA + 1):
                    url_alvo = f"{url_base}?page={pag}" if pag > 1 else url_base
                    print(f"\n🌐 [Robô]: Varrendo {marca.upper()} -> Página {pag}/{PAGINAS_POR_MARCA}...")
                    
                    try:
                        await page.goto(url_alvo, wait_until="networkidle", timeout=30000)
                        
                        # Rolagem para Lazy Load
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
                        await asyncio.sleep(1)
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                        await asyncio.sleep(1)
                        
                        elementos = await page.locator("a, div").all_inner_texts()
                        dados_pagina = []
                        
                        for texto in elementos:
                            linha = texto.strip().replace("\n", " ")
                            
                            if "preço: us$" in linha.lower() and marca in linha.lower():
                                if re.match(r"^\d{4}", linha):
                                    for alvo in ALVOS_ESTRITOS:
                                        padrao = r"\b" + re.escape(alvo) + r"\b"
                                        if re.search(padrao, linha.lower()):
                                            if linha not in dados_pagina:
                                                dados_pagina.append(linha)
                                            break
                        
                        print(f"   📊 Encontrados {len(dados_pagina)} candidatos válidos nesta página.")
                        
                        for carro in dados_pagina:
                            try:
                                ano = re.search(r"^\d{4}", carro).group() if re.search(r"^\d{4}", carro) else "N/A"
                                preco_usd_str = re.search(r"Preço:\s*US\$\s*([\d.]+)", carro).group(1).replace(".", "")
                                preco_usd = float(preco_usd_str)
                                km_str = re.search(r"([\d.,]+)\s*km", carro, re.IGNORECASE).group(1).replace(",", "").replace(".", "")
                                km = int(km_str)
                                
                                transmissao = "Manual" if " mt " in carro.lower() or "manual" in carro.lower() else "Automatic"
                                preco_jpy = preco_usd * 150.0
                                
                                fim_titulo = carro.lower().find("km")
                                nome_modelo = carro[:fim_titulo-4].strip() if fim_titulo != -1 else f"{marca.capitalize()} JDM"
                                
                                url_carro = f"https://carused.jp/pt/car/{nome_modelo.lower().replace(' ', '-')}"
                                
                                # 🛠️ CORREÇÃO: Usando a classe correta CarListing maiúscula
                                existe = db.query(models.CarListing).filter(models.CarListing.url == url_carro).first()
                                if not existe:
                                    novo_registro = models.CarListing(
                                        model=f"{nome_modelo} ({ano})",
                                        auction_grade="Stock",
                                        mileage=km,
                                        price_jpy=preco_jpy,
                                        price_brl=preco_usd * 5.20,
                                        price_usd=preco_usd,
                                        transmission=transmissao,
                                        url=url_carro
                                    )
                                    db.add(novo_registro)
                                    total_novos_carros += 1
                                    print(f"      ➕ [Adicionado]: {nome_modelo} ({ano})")
                            except Exception:
                                continue
                                
                    except Exception as page_err:
                        print(f"   ❌ Erro ao processar a página {pag}: {page_err}")
                        continue
                        
            if total_novos_carros > 0:
                db.commit()
                print(f"\n✨ [Sucesso]: Varredura de páginas concluída! {total_novos_carros} novos registros adicionados.")
            else:
                print("\n💤 Nenhum JDM inédito nas páginas varridas.")
                
        finally:
            await browser.close()

# Para rodar o arquivo isolado pelo terminal se quiser testar sem o FastAPI
if __name__ == "__main__":
    from database import SessionLocal  # Import local apenas para teste isolado
    database_session = SessionLocal()
    try:
        asyncio.run(garimpar_carused_completo(database_session))
    finally:
        database_session.close()