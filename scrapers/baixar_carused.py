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
    print("🤖 [jdm-spec-scout]: Iniciando Varredura Avançada com Sincronização na Carused...")
    
    FONTES_MARCAS = {
        "mazda": "https://carused.jp/pt/car-list/mazda",
        "toyota": "https://carused.jp/pt/car-list/toyota",
        "nissan": "https://carused.jp/pt/car-list/nissan",
        "mitsubishi": "https://carused.jp/pt/car-list/mitsubishi",
        "subaru": "https://carused.jp/pt/car-list/subaru"
    }
    
    ALVOS_ESTRITOS = [
        "rx-7", "rx7", "rx-8", "rx8", "miata", "roadster",
        "supra", "ae86", "chaser", "mr2", "celica", "altezza", "gt86", "gt-86", "86", "zn6", "a90",
        "skyline", "gt-r", "gtr", "r35", "silvia", "180sx", "240sx", "fairlady", "350z", "370z", "400z", "300zx",
        "impreza", "wrx", "sti", "legacy b4", "brz", "zd8",
        "lancer", "evolution", "evo", "3000gt", "gto", "fto"
    ]
    
    PAGINAS_POR_MARCA = 3
    
    # 🛒 Nova lista para monitorar TUDO que está online hoje nesta varredura
    urls_ativas_hoje = []

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
                                
                                # Guardamos a URL na lista de ativos do dia
                                urls_ativas_hoje.append(url_carro)
                                
                                existe = db.query(models.CarListing).filter(models.CarListing.url == url_carro).first()
                                if not existe:
                                    novo_registro = models.CarListing(
                                        carro=nome_modelo,        # Ajustado para mapear com o seu banco real
                                        ano_mes=f"{ano}/1",       # Ajustado para o padrão do banco
                                        preco=f"USD {preco_usd:,.0f}",
                                        quilometragem=f"{km:,}km",
                                        cambio=f"{transmissao} (MT)" if transmissao == "Manual" else "Automatic (AT)",
                                        cor="N/A",                # O robô pega a cor depois ou deixa padrão
                                        localizacao="JAPAN",
                                        fonte="Carused",          # Identificador da fonte para a limpeza
                                        stock_id=f"CU{km:5d}"     # Gera um ID temporário se não achar na linha
                                    )
                                    db.add(novo_registro)
                                    total_novos_carros += 1
                                    print(f"      ➕ [Adicionado]: {nome_modelo} ({ano})")
                            except Exception:
                                continue
                                
                    except Exception as page_err:
                        print(f"   ❌ Erro ao processar a página {pag}: {page_err}")
                        continue
            
            # 🧹 --- ETAPA DE LIMPEZA (SINCRONIZAÇÃO) ---
            print("\n🧹 [Faxina]: Iniciando verificação de anúncios vendidos...")
            
            if urls_ativas_hoje:
                # Busca carros no banco que são da Carused mas a URL NÃO está na lista de hoje
                anuncios_antigos = db.query(models.CarListing).filter(
                    models.CarListing.fonte.ilike("%Carused%"),
                    ~models.CarListing.url.in_(urls_ativas_hoje)
                )
                
                total_deletado = anuncios_antigos.count()
                
                if total_deletado > 0:
                    anuncios_antigos.delete(synchronize_session=False)
                    print(f"    🗑️ [Limpeza]: {total_deletado} carros foram removidos do SQLite pois foram vendidos ou saíram do site!")
                else:
                    print("    ✅ [Limpeza]: Nenhum carro vendido detectado. Banco 100% em dia.")

            # Salva todas as alterações (inserções e deleções) de uma vez só
            db.commit()
            print(f"\n✨ [Sucesso]: Varredura e sincronização concluídas! {total_novos_carros} novos inseridos.")
                
        finally:
            await browser.close()

if __name__ == "__main__":
    from database import SessionLocal
    database_session = SessionLocal()
    try:
        asyncio.run(garimpar_carused_completo(database_session))
    finally:
        database_session.close()