import asyncio
from playwright.async_api import async_playwright

async def testar_carregamento_real():
    print("🤖 Abrindo navegador para ver o comportamento do Next.js...")
    async with async_playwright() as p:
        # Abrimos com headless=False para você ver o que está acontecendo
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Vamos direto para a listagem da Mazda
        url = "https://carused.jp/pt/car-list/mazda"
        print(f"🌐 Acessando: {url}")
        await page.goto(url, wait_until="networkidle")
        
        # Espera 5 segundos para a renderização do Next.js acontecer na tela
        print("⏳ Aguardando renderização dos scripts dinâmicos...")
        await asyncio.sleep(5)
        
        # Vamos rolar a tela devagar para forçar o carregamento dos cards
        print("📜 Rolando a página para ativar o carregamento...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3);")
        await asyncio.sleep(2)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 1.5);")
        await asyncio.sleep(2)
        
        # Agora vamos extrair TODOS os links que existem na página DEPOIS do carregamento
        links = await page.locator("a").all()
        print(f"📊 Total de links encontrados dinamicamente: {len(links)}")
        
        # Vamos printar os links que NÃO são do menu institucional para ver o padrão dos carros
        encontrados = 0
        for link in links:
            href = await link.get_attribute("href") or ""
            texto = await link.inner_text()
            texto = texto.strip().replace("\n", " ")
            
            # Se o link tiver texto longo (nome do carro) ou fugir do padrão institucional:
            if "/pt/" in href and len(href) > 5 and "static" not in href and "feature" not in href and "auction" not in href:
                if len(texto) > 10:  # Evita links vazios ou ícones
                    encontrados += 1
                    print(f"Carro {encontrados}: href='{href}' | Texto: {texto[:80]}")
                    
        if encontrados == 0:
            print("❌ Mesmo com o navegador aberto, nenhum card de carro foi renderizado no DOM.")
            
        await browser.close()

asyncio.run(testar_carregamento_real())