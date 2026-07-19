import asyncio
import re
import sys
import os
from playwright.async_api import async_playwright
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import models

async def garimpar_carused_completo(db: Session):
    print("🤖 [jdm-spec-scout]: Iniciando Varredura Cirúrgica via Rotas Oficiais...")
    
    ALVOS_ESTRUTOS = {
        "mazda": ["rx-7", "rx-8", "roadster"],
        "toyota": ["supra", "mr2", "celica", "altezza", "86"],
        "nissan": ["skyline", "gt-r", "silvia", "180sx", "fairlady-z", "350z", "370z"],
        "subaru": ["impreza", "wrx", "wrx-sti", "brz"],
        "mitsubishi": ["lancer", "gto", "fto"]
    }
    
    PAGINAS_POR_MODELO = 2
    urls_ativas_hoje = []
    total_processados = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            for marca, modelos in ALVOS_ESTRUTOS.items():
                for modelo in modelos:
                    for pag in range(1, PAGINAS_POR_MODELO + 1):
                        
                        if pag == 1:
                            url_alvo = f"https://carused.jp/pt/car-list/{marca}/{modelo}?sort=did"
                        else:
                            url_alvo = f"https://carused.jp/pt/car-list/{marca}/{modelo}?sort=did&page={pag}"
                        
                        print(f"\n🎯 [Robô]: Acessando rota oficial -> {marca.upper()} {modelo.upper()} (Pág. {pag})")
                        
                        try:
                            await page.goto(url_alvo, wait_until="networkidle", timeout=30000)
                            await asyncio.sleep(2)
                            
                            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
                            await asyncio.sleep(1)
                            
                            cards = await page.locator('a[href*="/pt/car-list/detail/"]').all()
                            dados_pagina = []
                            
                            for card in cards:
                                texto_card = await card.inner_text()
                                href = await card.get_attribute("href")
                                if not texto_card or not href: continue
                                    
                                linha = texto_card.strip().replace("\n", " ")
                                if (linha, href) not in dados_pagina:
                                    dados_pagina.append((linha, href))
                            
                            print(f"   📊 Encontrados {len(dados_pagina)} carros listados nesta rota.")
                            
                            for carro_texto, url_completa in dados_pagina:
                                # Filtro de segurança: ignora anúncios que não correspondem ao modelo da busca
                                if marca.lower() not in carro_texto.lower() and modelo.replace("-", "").lower() not in carro_texto.lower():
                                    continue

                                try:
                                    ano_match = re.search(r"\b(19\d{2}|20\d{2})\b", carro_texto)
                                    ano = ano_match.group() if ano_match else "N/A"
                                    
                                    preco_match = re.search(r"US\$\s*([\d,.]+)", carro_texto, re.IGNORECASE)
                                    preco_usd = "Sob Consulta"
                                    if preco_match:
                                        limpo = preco_match.group(1).replace(",", "").replace(".", "")
                                        if len(limpo) <= 4: limpo = limpo.ljust(4, '0')
                                        preco_usd = f"USD {int(limpo):,}"
                                    
                                    km_match = re.search(r"([\d.,]+)\s*km", carro_texto, re.IGNORECASE)
                                    km = "N/A"
                                    if km_match:
                                        km_limpa = km_match.group(1).replace(",", "").replace(".", "")
                                        km = f"{int(km_limpa):,}km"
                                    
                                    transmissao = "Manual (MT)" if " mt " in carro_texto.lower() else "Automatic (AT)"
                                    nome_modelo = carro_texto.split("km")[0].strip() if "km" in carro_texto.lower() else carro_texto
                                    nome_modelo = re.sub(r"^\d{4}\s+", "", nome_modelo)
                                    
                                    url_carro = url_completa if url_completa.startswith("http") else f"https://carused.jp{url_completa}"
                                    urls_ativas_hoje.append(url_carro)
                                    
                                    ref_match = url_carro.split("/")[-1]
                                    stock_id = ref_match if ref_match else "CU-UNKNOWN"
                                    
                                    # Verifica se já existe no banco para evitar conflitos de UNIQUE
                                    existente = db.query(models.CarListing).filter_by(stock_id=stock_id).first()
                                    
                                    if existente:
                                        existente.preco = preco_usd
                                        existente.quilometragem = km
                                    else:
                                        novo_registro = models.CarListing(
                                            carro=nome_modelo,
                                            ano_mes=f"{ano}/1",
                                            preco=preco_usd,
                                            quilometragem=km,
                                            cambio=transmissao,
                                            cor="N/A",
                                            localizacao="JAPAN",
                                            fonte="Carused",
                                            stock_id=stock_id,
                                            link=url_carro
                                        )
                                        db.add(novo_registro)
                                    
                                    db.commit()
                                    total_processados += 1
                                    print(f"   ✅ [Processado]: {stock_id}")
                                    
                                except Exception as e:
                                    db.rollback()
                                    print(f"   ❌ Erro ao processar carro: {e}")
                                    continue
                                    
                        except Exception as page_err:
                            print(f"   ❌ Erro ao processar rota {modelo}: {page_err}")
                            continue
            
            print("\n🧹 [Faxina]: Removendo anúncios antigos...")
            if urls_ativas_hoje:
                anuncios_antigos = db.query(models.CarListing).filter(
                    models.CarListing.fonte.ilike("%Carused%"),
                    ~models.CarListing.link.in_(urls_ativas_hoje)
                )
                total_deletado = anuncios_antigos.count()
                if total_deletado > 0:
                    anuncios_antigos.delete(synchronize_session=False)
                    db.commit()
                    print(f"   🗑️ [Limpeza]: {total_deletado} carros antigos removidos.")

            print(f"\n✨ Finalizado! Total de registros sincronizados: {total_processados}.")
                
        finally:
            await browser.close()

if __name__ == "__main__":
    from database import SessionLocal, engine
    models.Base.metadata.create_all(bind=engine)
    database_session = SessionLocal()
    try:
        asyncio.run(garimpar_carused_completo(database_session))
    finally:
        database_session.close()