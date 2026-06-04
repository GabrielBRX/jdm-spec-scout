import asyncio
import re
from playwright.async_api import async_playwright

async def garimpar_rx7_japao():
    print("🤖 [jdm-spec-scout]: Iniciando varredura especializada em RX-7...")
    URL_ALVO = "https://carused.jp/pt/car-list/mazda"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, 
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo"
        )
        
        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            print(f"🌐 [Robô]: Conectando à base de dados de JDM...")
            await page.goto(URL_ALVO, wait_until="networkidle", timeout=60000)
            
            
            print("📜 [Robô]: Forçando carregamento dinâmico dos cards...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
            await asyncio.sleep(2)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(2)
            
            
            elementos = await page.locator("a, div").all_inner_texts()
            
            estoque_rx7 = []
            
            
            print("🔍 [Robô]: Filtrando especificações técnicas por alvos...")
            for texto in elementos:
                linha = texto.strip().replace("\n", " ")
        
                
                if "preço: us$" in linha.lower() and "mazda" in linha.lower():
                    
                    if re.match(r"^\d{4}", linha): 
                
                        
                        if "rx-7" in linha.lower() or "rx7" in linha.lower():
                
                    
                                if linha not in estoque_rx7:
                                    estoque_rx7.append(linha)

            
            print(f"\n📊 [Resultado]: Encontrei {len(estoque_rx7)} Mazdas RX-7 disponíveis nesta página.")
            
            if estoque_rx7:
                print("\n🏎️  === MAZDAS RX-7 ENCONTRADOS NO JAPÃO ===")
                for i, carro in enumerate(estoque_rx7, 1):
                    
                    try:
                        ano = re.search(r"^\d{4}", carro).group() if re.search(r"^\d{4}", carro) else "N/A"
                        preco = re.search(r"Preço:\s*(US\$\s*[\d.]+)", carro).group(1) if re.search(r"Preço:\s*(US\$\s*[\d.]+)", carro) else "Sob Consulta"
                        km = re.search(r"([\d.,]+\s*km)", carro, re.IGNORECASE).group(1) if re.search(r"([\d.,]+\s*km)", carro, re.IGNORECASE) else "N/A"
                        
                        print(f"\n🔥 [Carro #{i}]:")
                        print(f"   🔹 Modelo Completo: {carro[:80]}...") 
                        print(f"   📅 Ano: {ano}")
                        print(f"   🛣️  Quilometragem: {km}")
                        print(f"   💰 Preço: {preco}")
                    except Exception:
                        print(f"\n🔥 [Carro #{i} (Texto Bruto)]: {carro}")
            else:
                print("\n⚠️ [Aviso]: Nenhum RX-7 listado na primeira página de estoque hoje.")
                print("💡 Dica: O mercado de JDM está super aquecido, os modelos Spirit R e Type R somem em minutos!")
                
        except Exception as e:
            print(f"❌ [Robô]: Erro durante o processamento do inventário: {e}")
            
        finally:
            await browser.close()
            print("\n🔒 [Robô]: Sistema desconectado com segurança.")

if __name__ == "__main__":
    asyncio.run(garimpar_rx7_japao())