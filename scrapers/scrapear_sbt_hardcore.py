import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def executar_scraper_hardcore():
    print("🔥 [jdm-spec-scout]: Iniciando o modo HÍBRIDO Humano + Robô...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            no_viewport=True
        )
        
        page = await context.new_page()
        
        print("🏠 Acessando a Home Page...")
        await page.goto("https://www.sbtjapan.com/", wait_until="domcontentloaded", timeout=60000)
        
        # Tenta fechar cookies automaticamente bem rápido de fundo
        try:
            botao_cookie = page.locator("button:has-text('Accept'), #onetrust-accept-btn-handler").first
            if await botao_cookie.is_visible(timeout=3000):
                await botao_cookie.click()
                print("🍪 Cookies aceitos automaticamente.")
        except:
            pass

        # === JANELA DE INTERAÇÃO HUMANA ===
        print("\n==============================================================")
        print("🎯 AGORA É COM VOCÊ, GABRIEL!")
        print("Você tem 30 SEGUNDOS para interagir com o navegador:")
        print("1. Aceite os cookies (se o robô não aceitou).")
        print("2. Faça a busca pelo Mazda RX-7 usando os filtros ou o botão correto.")
        print("3. DEIXE A PÁGINA EXIBINDO A LISTA DE CARROS DOS RX-7.")
        print("==============================================================\n")
        
        # Contagem regressiva no terminal para você acompanhar o tempo
        for i in range(30, 0, -1):
            if i % 5 == 0 or i <= 5:
                print(f"⏳ Tempo restante para você preparar a página: {i} segundos...")
            await asyncio.sleep(1)
            
        print("\n⚡ Tempo esgotado! O robô vai assumir e capturar os dados agora...")
        
        # Faz uma rolagem para baixo para carregar imagens ou elementos lazy-load
        await page.evaluate("window.scrollBy(0, 500);")
        await asyncio.sleep(2)
        
        # Captura o HTML do jeito que estiver na sua tela
        html_content = await page.content()
        await browser.close()
        
    # --- PARTE 2: SUPER PARSER ---
    print("🧙‍♂️ [BeautifulSoup]: Fazendo a varredura profunda na página que você buscou...")
    soup = BeautifulSoup(html_content, "html.parser")
    lista_carros = []
    
    # Mapeando absolutamente qualquer tag ou container que o SBT use para listar carros
    cards = soup.select(".car-list-row, .car-item, .vehicle-card, tr.search-result-item, .car-info-box, .car_list_box")
    print(f"📊 Blocos estruturados detectados: {len(cards)}")
    
    if len(cards) == 0:
        print("🕵️‍♂️ Varredura estruturada retornou 0. Iniciando extração adaptativa por links de JDM...")
        # Se os seletores falharem, varremos todas as tags 'a' e divs atrás de referências a carros
        for link in soup.find_all("a"):
            texto = link.get_text().lower()
            if "rx-7" in texto or "mazda" in texto or "fd3s" in texto:
                parent = link.find_parent("div") or link
                lista_carros.append({
                    "modelo": link.get_text().strip(),
                    "preco": "Consultar no Bloco",
                    "dados_gerais": parent.get_text(separator=" ").strip()[:200]
                })
    else:
        for card in cards:
            try:
                nome = card.select_one(".car-name, .title, h2, .vehicle-name, .car_name").text.strip() if card.select_one(".car-name, .title, h2, .vehicle-name, .car_name") else "N/A"
                preco = card.select_one(".price, .fob-price, .car-price, .fob, .price_box").text.strip() if card.select_one(".price, .fob-price, .car-price, .fob, .price_box") else "N/A"
                lista_carros.append({
                    "modelo": nome,
                    "preco": preco,
                    "dados_gerais": card.get_text(separator=" ").replace("\n", " ").strip()[:200]
                })
            except:
                continue

    # Removendo duplicatas da busca adaptativa
    lista_carros = [dict(t) for t in {tuple(d.items()) for d in lista_carros}]

    if lista_carros:
        with open("resultados_finais_rx7.json", "w", encoding="utf-8") as f:
            json.dump(lista_carros, f, indent=4, ensure_ascii=False)
        print(f"🎉 SUCESSO! Conseguimos extrair {len(lista_carros)} registros para o seu arquivo 'resultados_finais_rx7.json'!")
    else:
        print("💀 Mesmo com a busca manual, não conseguimos extrair elementos válidos.")
        with open("html_analise.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("💾 HTML salvo em 'html_analise.html' para inspecionarmos as tags.")

if __name__ == "__main__":
    asyncio.run(executar_scraper_hardcore())