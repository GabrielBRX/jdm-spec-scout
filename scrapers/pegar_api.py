import asyncio
from playwright.async_api import async_playwright

async def espionar_rede():
    print("🕵️‍♂️ [jdm-spec-scout]: Espionando TODAS as requisições do site...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Esse bloco vai printar no terminal absolutamente TUDO que o site chamar
        async def monitorar(response):
            # Filtra apenas requisições do tipo fetch/xhr ou que pareçam trazer dados (ignora imagens/css)
            if response.request.resource_type in ["fetch", "xhr"]:
                print(f"🔗 Chamada detectada: {response.url} | Status: {response.status}")

        page.on("response", monitorar)
        
        url_busca = "https://www.sbtjapan.com/used-cars/?keyword=rx-7"
        await page.goto(url_busca, wait_until="domcontentloaded", timeout=60000)
        
        # Deixei 20 segundos para a página carregar tudo com calma
        print("⏳ Monitorando a rede por 20 segundos... Olhe o seu terminal!")
        await asyncio.sleep(20)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(espionar_rede())