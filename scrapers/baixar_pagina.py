import time
from playwright.sync_api import sync_playwright

def salvar_dump_geral():
    url = "https://www.sbtjapan.com/used-cars?keyword=Toyota+SUPRA"
    print(f"📥 Baixando HTML de teste para análise...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        time.sleep(6)
        
        with open("resultado_dump.html", "w", encoding="utf-8") as f:
            f.write(page.content())
            
        print("✅ Arquivo 'resultado_dump.html' salvo na raiz!")
        browser.close()

if __name__ == "__main__":
    salvar_dump_geral()