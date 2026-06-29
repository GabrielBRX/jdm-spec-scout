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
    
    # Lista estrita de lendas JDM
    ALVOS_ESTRITOS = [
        "rx-7", "rx7", "rx-8", "rx8", "miata", "roadster",
        "supra", "ae86", "chaser", "mr2", "celica", "altezza", "gt86", "gt-86", "86", "zn6", "a90",
        "skyline", "gt-r", "gtr", "r35", "silvia", "180sx", "240sx", "fairlady", "350z", "370z", "400z", "300zx",
        "impreza", "wrx", "sti", "legacy b4", "brz", "zd8",
        "lancer", "evolution", "evo", "3000gt", "gto", "fto"
    ]
    
    PAGINAS_POR_MARCA = 3  # Quantas páginas você quer varrer por marca?
    
    # 🛒 Lista para monitorar TODOS os Stock IDs reais ativos hoje nesta varredura
    ids_ativos_hoje = []

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
                        
                        # Rolagem inteligente para carregar conteúdo (Lazy Load)
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
                        await asyncio.sleep(1)
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                        await asyncio.sleep(1)
                        
                        # 🎯 CAPTURA DINÂMICA via links <a>
                        links = await page.locator("a").all()
                        dados_pagina = []
                        
                        for link in links:
                            texto_link = await link.inner_text()
                            if not texto_link:
                                continue
                                
                            linha = texto_link.strip().replace("\n", " ")
                            linha_lower = linha.lower()
                            
                            if ("us$" in linha_lower or "preço" in linha_lower or "price" in linha_lower) and marca in linha_lower:
                                for alvo in ALVOS_ESTRITOS:
                                    padrao = r"\b" + re.escape(alvo) + r"\b"
                                    if re.search(padrao, linha_lower):
                                        
                                        # Captura a URL real apenas para usar se necessário (não salvamos no banco)
                                        url_real = await link.get_attribute("href") or ""
                                        
                                        item_com_dados = (linha, url_real)
                                        if item_com_dados not in dados_pagina:
                                            dados_pagina.append(item_com_dados)
                                        break
                        
                        print(f"   📊 Encontrados {len(dados_pagina)} candidatos válidos nesta página.")
                        
                        for carro, url_carro in dados_pagina:
                            try:
                                ano_match = re.search(r"\b(19\d{2}|20\d{2})\b", carro)
                                ano = ano_match.group(1) if ano_match else "N/A"
                                
                                preco_usd_str = re.search(r"(?:preço|price)?\s*:?\s*us\$\s*([\d.]+)", carro, re.IGNORECASE).group(1).replace(".", "")
                                preco_usd = float(preco_usd_str)
                                
                                km_str = re.search(r"([\d.,]+)\s*km", carro, re.IGNORECASE).group(1).replace(",", "").replace(".", "")
                                km = int(km_str)
                                
                                transmissao = "Manual" if " mt " in carro.lower() or "manual" in carro.lower() else "Automatic"
                                
                                # 🔑 GERAÇÃO DO STOCK ID: Como a Carused esconde o ID na listagem, vamos gerar um ID 
                                # baseado no modelo, ano e km para criar uma assinatura única e evitar duplicados.
                                fim_titulo = carro.lower().find("km")
                                nome_modelo = carro[:fim_titulo-4].strip() if fim_titulo != -1 else f"{marca.capitalize()} JDM"
                                nome_modelo = re.sub(r"^\d{4}\s*", "", nome_modelo)
                                
                                stock_id_real = f"CU-{marca[:2].upper()}-{ano}-{km}"
                                
                                cor_detectada = "N/A"
                                cores_comuns = ["white", "black", "silver", "blue", "red", "grey", "gray", "yellow"]
                                for c in cores_comuns:
                                    if c in carro.lower():
                                        cor_detectada = c.capitalize()
                                        break
                                
                                # Adiciona à lista de IDs ativos capturados hoje
                                ids_ativos_hoje.append(stock_id_real)
                                
                                # 🔍 CHECAGEM DE DUPLICADOS: Feita pelo stock_id como manda seu models.py
                                existe = db.query(models.CarListing).filter(models.CarListing.stock_id == stock_id_real).first()
                                if not existe:
                                    novo_registro = models.CarListing(
                                        stock_id=stock_id_real,
                                        carro=nome_modelo,
                                        ano_mes=f"{ano}/1",
                                        preco=f"USD {preco_usd:,.0f}",
                                        quilometragem=f"{km:,}km",
                                        cambio=f"{transmissao} (MT)" if transmissao == "Manual" else "Automatic (AT)",
                                        cor=cor_detectada,
                                        localizacao="JAPAN",
                                        fonte="Carused"  # Sobrescreve o default para marcar que veio da Carused!
                                    )
                                    db.add(novo_registro)
                                    total_novos_carros += 1
                                    print(f"      ➕ [Adicionado]: {nome_modelo} ({ano}) - Stock ID: {stock_id_real}")
                            except Exception:
                                continue
                                
                    except Exception as page_err:
                        print(f"   ❌ Erro ao acessar a página {pag}: {page_err}")
                        continue
            
            # 🧹 --- ETAPA DE FAXINA AUTOMÁTICA VIA STOCK ID ---
            print("\n🧹 [Faxina]: Iniciando verificação de anúncios vendidos...")
            if ids_ativos_hoje:
                anuncios_antigos = db.query(models.CarListing).filter(
                    models.CarListing.fonte == "Carused",
                    ~models.CarListing.stock_id.in_(ids_ativos_hoje)
                )
                total_deletado = anuncios_antigos.count()
                
                if total_deletado > 0:
                    anuncios_antigos.delete(synchronize_session=False)
                    print(f"    🗑️ [Limpeza]: {total_deletado} carros da Carused foram removidos pois saíram do site!")
                else:
                    print("    ✅ [Limpeza]: Nenhum carro vendido detectado. Banco 100% atualizado!")

            db.commit()
            
            if total_novos_carros > 0:
                print(f"\n✨ [Sucesso]: Sincronização concluída! {total_novos_carros} novos registros adicionados.")
            else:
                print("\n💤 Sincronização concluída. Nenhum JDM inédito encontrado.")
                
        finally:
            await browser.close()