import time
from playwright.sync_api import sync_playwright

def gerar_dump():
    url = "https://www.sbtjapan.com/used-cars?keyword=Toyota+SUPRA"
    print(f"📥 Acessando e gerando o dump HTML de: {url}")
    
    with sync_playwright() as p:
        # Usamos headless=False para você ver o navegador abrindo e carregando
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            print("⏳ Aguardando 8 segundos para a página renderizar completamente...")
            time.sleep(8)
            
            # Salva o HTML completo
            html_content = page.content()
            with open("sbt_dump_real.html", "w", encoding="utf-8") as f:
                f.write(html_content)
                
            print("✅ Sucesso! Arquivo 'sbt_dump_real.html' gerado na raiz do projeto.")
        except Exception as e:
            print(f"❌ Erro ao carregar a página: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    gerar_dump()
    