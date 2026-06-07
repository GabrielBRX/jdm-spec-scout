import asyncio
import re
import sys
import os
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import SessionLocal
import models

async def garimpar_sbt_japan():
    print("🤖 [jdm-spec-scout]: Ativando Motor por Injeção de DOM Sincronizado...")
    
    TERMOS_BUSCA = [
        "rx-7", "rx-8", "supra", "ae86", "chaser", "mr2", "celica", 
        "skyline", "silvia", "180sx", "fairlady z", "350z", "370z", 
        "wrx sti", "impreza", "legacy b4", "brz", "gt86", "lancer evolution"
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        await context.add_cookies([{
            "name": "SBT_COUNTRY_CODE", "value": "BR", "domain": ".sbtjapan.com", "path": "/"
        }, {
            "name": "sbt_country", "value": "brazil", "domain": ".sbtjapan.com", "path": "/"
        }])
        
        page = await context.new_page()
        db = SessionLocal()
        total_sbt = 0
        
        try:
            for modelo in TERMOS_BUSCA:
                url_busca = f"https://www.sbtjapan.com/used-cars/?keyword={modelo.replace(' ', '%20')}"
                print(f"\n🌐 [SBT]: Verificando estoque para -> '{modelo.upper()}'...")
                
                try:
                    await page.goto(url_busca, wait_until="load", timeout=45000)
                    
                    # 🎯 VALIDAÇÃO DE ESTOQUE REAL: Espera o elemento de KM indicar que há listagem ativa
                    try:
                        # Reduzimos para 5s para o script rodar mais rápido caso esteja zerado
                        await page.wait_for_selector("text=km", timeout=5000)
                    except:
                        print(f"   🚫 [SEM ESTOQUE]: Nenhum '{modelo.upper()}' disponível no SBT Japan hoje. Pulando...")
                        continue # 🧠 Pula direto para o próximo modelo da lista!
                        
                    await asyncio.sleep(1)
                    await page.evaluate("window.scrollTo(0, 400);")

                    # Injeção JS que extrai a URL e o texto renderizado
                    cards_com_dados = await page.evaluate('''() => {
                        let resultados = [];
                        let links = document.querySelectorAll('a[href*="/used-cars/"]');
                        
                        links.forEach(link => {
                            let href = link.getAttribute('href') || "";
                            if (href.includes('id=') && !href.includes('why-choose') && !href.includes('how-to-buy')) {
                                let container = link.closest('.car-list-row, .carList_box, tr, div[class*="box"], div[class*="item"]');
                                if (!container) {
                                    container = link.parentElement?.parentElement?.parentElement;
                                }
                                if (container && container.innerText.trim().length > 20) {
                                    resultados.push({ url: href, texto: container.innerText });
                                }
                            }
                        });
                        return resultados;
                    }''')

                    if not cards_com_dados:
                        print(f"   📊 Nenhum card com conteúdo textual foi localizado no DOM.")
                        continue

                    vistos = set()
                    cards_filtrados = []
                    for c in cards_com_dados:
                        if c['url'] not in vistos:
                            vistos.add(c['url'])
                            cards_filtrados.append(c)

                    print(f"   📊 Encontrados {len(cards_filtrados)} cards carregados. Processando...")
                    
                    for card in cards_filtrados:
                        try:
                            texto_bloco = card['texto'].strip().replace("\n", " ")
                            texto_lower = texto_bloco.lower()
                            
                            # 🛠️ EXTRAÇÃO DE PREÇO SECO
                            precos = re.findall(r"(?:USD|\$)\s*([\d.,]+)", texto_bloco, re.IGNORECASE)
                            valores = []
                            for p in precos:
                                try:
                                    if "," in p and "." in p:
                                        p_limpo = p.replace(",", "") if p.find(",") < p.find(".") else p.replace(".", "").replace(",", ".")
                                    else:
                                        p_limpo = p.replace(",", "")
                                    valores.append(float(p_limpo))
                                except Exception:
                                    continue
                            
                            valores_validos = [v for v in valores if 500 <= v <= 350000]
                            preco_usd = max(valores_validos) if valores_validos else 0.0
                            
                            # 🛠️ EXTRAÇÃO DE ANO
                            ano_match = re.search(r"\b(19[89]\d|20[0-2]\d)\b", texto_bloco)
                            ano = ano_match.group() if ano_match else "N/A"
                            
                            # 🛠️ EXTRAÇÃO DE KM
                            km_match = re.search(r"([\d.,]+)\s*(?:km|kms)", texto_bloco, re.IGNORECASE)
                            km = int(km_match.group(1).replace(",", "").replace(".", "")) if km_match else 0

                            print(f"      🔍 [AUDITORIA]: Ano: {ano} | KM: {km} | Preço: USD {preco_usd}")

                            if preco_usd == 0.0 or km == 0:
                                continue
                                
                            transmissao = "Manual" if "mt" in texto_lower or "manual" in texto_lower else "Automatic"
                            preco_jpy = preco_usd * 150.0
                            
                            url_relativa = card['url']
                            url_final = f"https://www.sbtjapan.com{url_relativa}" if url_relativa.startswith("/") else url_relativa
                            
                            nome_final = f"{modelo.upper()} SBT-Spec"
                            
                            existe = db.query(models.carlisting).filter(models.carlisting.url == url_final).first()
                            
                            if not existe:
                                novo_registro = models.carlisting(
                                    model=f"{nome_final} ({ano})",
                                    auction_grade="SBT Stock",
                                    mileage=km,
                                    price_jpy=preco_jpy,
                                    price_brl=preco_usd * 5.40,
                                    price_usd=preco_usd,
                                    transmission=transmissao,
                                    url=url_final
                                )
                                db.add(novo_registro)
                                total_sbt += 1
                                print(f"      ➕ [BANCO]: {nome_final} ({ano}) -> USD {preco_usd} | {km:,} km")
                        except Exception:
                            continue
                            
                except Exception as e:
                    print(f"   ❌ Erro de processamento no termo {modelo}: {e}")
                    continue
            
            if total_sbt > 0:
                db.commit()
                print(f"\n✨ [Sucesso SBT]: Sincronização Concluída! {total_sbt} carros salvos.")
            else:
                print("\n💤 Sincronização finalizada. Sem novos anúncios pendentes.")
                
        finally:
            db.close()
            await browser.close()
            print("🔒 [Robô]: Navegador encerrado com segurança.")

if __name__ == "__main__":
    asyncio.run(garimpar_sbt_japan())