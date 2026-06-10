import asyncio
import random
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def humano_espera(min_tempo=1, max_tempo=3):
    """Gera uma pausa aleatória para quebrar padrões robóticos."""
    await asyncio.sleep(random.uniform(min_tempo, max_tempo))

async def executar_scraper_hardcore():
    print("🔥 [jdm-spec-scout]: Iniciando a operação 'Tudo ou Nada' contra o SBT Japan...")
    
    async with async_playwright() as p:
        # Abrindo o navegador visível e simulando uma tela Full HD padrão
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        
        # Criando o contexto simulando um Windows 10 real com Chrome atualizado
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            no_viewport=True # Deixa o navegador usar o tamanho máximo real da tela
        )
        
        page = await context.new_page()
        
        # Passo 1: Entrar na Home limpa
        print("🏠 Acessando a Home Page...")
        await page.goto("https://www.sbtjapan.com/", wait_until="load", timeout=90000)
        await humano_espera(3, 5)
        
        # Passo 2: Aceitar a "bosta" dos Cookies
        print("🍪 Procurando aviso de cookies para fechar...")
        seletores_cookies = [
            "button:has-text('Accept')", "button:has-text('Agree')", 
            "button:has-text('Aceitar')", "#onetrust-accept-btn-handler", 
            ".cookie-accept", ".cookie-btn", "#btn-cookie-accept"
        ]
        
        for seletor in seletores_cookies:
            try:
                botao_cookie = page.locator(seletor).first
                if await botao_cookie.is_visible(timeout=2000):
                    print(f"🎯 Botão de cookie encontrado ({seletor})! Clicando...")
                    await botao_cookie.click()
                    await humano_espera(1, 2)
                    break
            except:
                continue

        # Simula uma rolada de página de leve e mexe o mouse para o site achar que é um humano mexendo
        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        await page.evaluate("window.scrollBy(0, 300);")
        await humano_espera(2, 3)
        await page.evaluate("window.scrollBy(0, -300);")
        
        # Passo 3: Interagir com a Barra de Busca
        print("🔍 Procurando a barra de pesquisa de forma dinâmica...")
        # Lista de possíveis seletores para a barra de busca deles
        seletores_busca = ["input[id='searchKey']", "input[name='keyword']", "input[type='search']", ".search-input"]
        campo_busca = None
        
        for seletor in seletores_busca:
            try:
                el = page.locator(seletor).first
                if await el.is_visible(timeout=3000):
                    campo_busca = el
                    print(f"📌 Barra de busca localizada via seletor: '{seletor}'")
                    break
            except:
                continue
                
        if campo_busca:
            # Move o mouse até a barra e clica
            await campo_busca.scroll_into_view_if_needed()
            box = await campo_busca.bounding_box()
            if box:
                await page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
            await campo_busca.click()
            await humano_espera(1, 2)
            
            # Digita como um humano (atraso aleatório entre cada letra)
            print("⌨️ Digitando 'rx-7' com ritmo humano...")
            for letra in "rx-7":
                await campo_busca.type(letra, delay=random.randint(150, 450))
            
            await humano_espera(1, 1.5)
            print("⚡ Pressionando Enter para buscar...")
            await campo_busca.press("Enter")
        else:
            print("⚠️ Não achei a barra visualmente. Forçando Plano B: Indo direto para a URL de resultados...")
            await page.goto("https://www.sbtjapan.com/used-cars/?keyword=rx-7", wait_until="networkidle", timeout=60000)
            
        # Passo 4: Espera crucial pós-busca
        print("⏳ Aguardando a página carregar e os scripts injetarem os carros...")
        await page.wait_for_load_state("networkidle", timeout=30000)
        # Mais um scroll para ativar lazy loading (carregamento por rolagem) caso exista
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3);")
        await humano_espera(5, 8)
        
        # Captura o HTML final gerado por todo esse processo
        html_content = await page.content()
        await browser.close()
        
    # --- PARTE 2: SUPER PARSER ---
    print("🧙‍♂️ [BeautifulSoup]: Iniciando varredura profunda no HTML...")
    soup = BeautifulSoup(html_content, "html.parser")
    
    lista_carros = []
    
    # Seletores estruturados conhecidos do SBT
    cards = soup.select(".car-list-row, .car-item, .vehicle-card, tr.search-result-item, .car-info-box")
    print(f"📊 Blocos de carros encontrados por seletores padrão: {len(cards)}")
    
    # Se os seletores falharem, vamos apelar para uma busca cega por texto de quilometragem/ano nos links!
    if len(cards) == 0:
        print("🕵️‍♂️ Alerta: Seletores estruturados falharam. Iniciando varredura cega por links...")
        # Procura por links que possam ser os detalhes dos carros
        links = soup.find_all("a")
        for link in links:
            texto = link.get_text().lower()
            # Se o link falar de RX-7 ou ter km/ano dentro, nós pegamos!
            if "rx-7" in texto or "mazda" in texto or "km" in texto:
                parent = link.find_parent("div") or link
                lista_carros.append({
                    "modelo": link.get_text().strip(),
                    "preco": "Verificar no link",
                    "dados_gerais": parent.get_text(separator=" ").strip()[:200]
                })
    else:
        # Extração se ele achou os blocos certinhos
        for card in cards:
            try:
                nome = card.select_one(".car-name, .title, h2, .vehicle-name").text.strip() if card.select_one(".car-name, .title, h2, .vehicle-name") else "N/A"
                preco = card.select_one(".price, .fob-price, .car-price, .fob").text.strip() if card.select_one(".price, .fob-price, .car-price, .fob") else "N/A"
                lista_carros.append({
                    "modelo": nome,
                    "preco": preco,
                    "dados_gerais": card.get_text(separator=" ").replace("\n", " ").strip()[:150]
                })
            except:
                continue

    # Salvando os resultados finais de tudo que conseguimos sugar do site
    if lista_carros:
        with open("resultados_finais_rx7.json", "w", encoding="utf-8") as f:
            json.dump(lista_carros, f, indent=4, ensure_ascii=False)
        print(f"🎉 FIM DA OPERAÇÃO! Conseguimos coletar {len(lista_carros)} registros no arquivo 'resultados_finais_rx7.json'!")
    else:
        print("💀 O SBT Japan nos bloqueou completamente no servidor deles. Nem o HTML inicial continha dados.")
        with open("html_bloqueado.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("💾 HTML gravado em 'html_bloqueado.html' para autópsia.")

if __name__ == "__main__":
    asyncio.run(executar_scraper_hardcore())