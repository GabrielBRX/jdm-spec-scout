import asyncio
from playwright.async_api import async_playwright

async def baixar():
    print("🌐 [jdm-spec-scout]: Acessando o SBT Japan para capturar o HTML real...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        
        # Cookies para passar pelo pop-up de país
        await context.add_cookies([
            {"name": "SBT_COUNTRY_CODE", "value": "BR", "domain": ".sbtjapan.com", "path": "/"},
            {"name": "sbt_country", "value": "brazil", "domain": ".sbtjapan.com", "path": "/"}
        ])
        
        page = await context.new_page()
        
        # 🏎️ Buscando o RX-7
        url_busca = "https://www.sbtjapan.com/used-cars/?keyword=rx-7"
        
        # 1. Mudamos para 'networkidle' para esperar os scripts paralelos terminarem de carregar os dados
        await page.goto(url_busca, wait_until="networkidle", timeout=60000)
        
        # 2. Simulação humana: Espera o esqueleto do site e tenta validar se os carros brotaram
        try:
            print("⏳ Aguardando renderização do grid de veículos...")
            # Espera até 15 segundos por qualquer container comum de listagem ou tabela
            await page.wait_for_selector(".car-list, .search-results, table, .car-list-row", timeout=15000)
            print("🎯 Boa! O container principal foi detectado.")
        except:
            print("⚠️ Aviso: O container demorou. Forçando scroll para ativar o carregamento dinâmico...")
            # Dá um scroll parcial na tela caso o site use lazy loading (carregar ao rolar)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 4);")
            
        # 3. Descanso final de segurança para o DOM se estabilizar por completo
        await asyncio.sleep(5)
        
        # Captura o HTML com tudo que foi injetado na tela
        html = await page.content()
        
        # Salva o arquivo final
        with open("sbt_rx7.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("💾 [Sucesso]: Arquivo 'sbt_rx7.html' atualizado na raiz do projeto com a nova lógica!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(baixar())