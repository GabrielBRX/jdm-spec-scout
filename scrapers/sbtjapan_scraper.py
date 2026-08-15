import sqlite3
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def salvar_no_banco(carros):
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS car_listings")
    cursor.execute("""
        CREATE TABLE car_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT,
            carro TEXT,
            ano_mes TEXT,
            preco TEXT,
            quilometragem TEXT,
            cambio TEXT,
            cor TEXT,
            localizacao TEXT,
            fonte TEXT,
            link TEXT,
            foto TEXT
        )
    """)
    
    for c in carros:
        cursor.execute("""
            INSERT INTO car_listings (stock_id, carro, ano_mes, preco, quilometragem, cambio, cor, localizacao, fonte, link, foto)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c.get('stock_id', 'N/A'),
            c.get('carro', 'N/A'),
            c.get('ano_mes', 'N/A'),
            c.get('preco', 'Sob Consulta'),
            c.get('quilometragem', 'N/A'),
            c.get('cambio', 'Manual'),
            c.get('cor', 'N/A'),
            c.get('localizacao', 'JAPAN'),
            'SBT Japan',
            c.get('link', '#'),
            c.get('foto', '')
        ))
    
    conn.commit()
    conn.close()
    print(f"💾 Total de {len(carros)} carros salvos com sucesso no banco!")

def raspar_sbt_japan():
    print("🚗 [SBT Japan] Iniciando raspagem com tratamento inteligente de hífens...")
    
    # Cada item mapeia o termo digitado no site e as variações aceitas no texto do card
    buscas = [
        {"termo_busca": "SUPRA", "variacoes": ["supra"]},
        {"termo_busca": "AE86", "variacoes": ["ae86", "corolla"]},
        {"termo_busca": "CHASER", "variacoes": ["chaser"]},
        {"termo_busca": "SOARER", "variacoes": ["soarer"]},
        {"termo_busca": "SILVIA", "variacoes": ["silvia"]},
        {"termo_busca": "GT-R", "variacoes": ["gt-r", "gtr"]},
        {"termo_busca": "SKYLINE", "variacoes": ["skyline"]},
        {"termo_busca": "FAIRLADY Z", "variacoes": ["fairlady", "z"]},
        {"termo_busca": "RX-7", "variacoes": ["rx-7", "rx7"]},
        {"termo_busca": "RX-8", "variacoes": ["rx-8", "rx8"]},
        {"termo_busca": "LANCER", "variacoes": ["lancer"]},
        {"termo_busca": "GTO", "variacoes": ["gto"]},
        {"termo_busca": "IMPREZA", "variacoes": ["impreza"]},
        {"termo_busca": "BRZ", "variacoes": ["brz"]},
        {"termo_busca": "WRX", "variacoes": ["wrx"]}
    ]
    
    lista_geral = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        url_base = "https://www.sbtjapan.com/used-cars"
        print(f"🌐 Acessando página base: {url_base}")
        
        try:
            page.goto(url_base, timeout=60000, wait_until="domcontentloaded")
            time.sleep(4)
        except Exception as e:
            print(f"❌ Erro ao carregar página base: {e}")
            browser.close()
            return

        for item in buscas:
            termo = item["termo_busca"]
            variacoes = item["variacoes"]
            
            print(f"🔍 Pesquisando modelo via input do site: {termo}...")
            try:
                search_input = page.locator("#keywordSearchInput")
                search_input.click()
                search_input.fill("")
                search_input.fill(termo)
                
                page.locator("#keywordSearchForm button.search-form__button").click()
                page.wait_for_load_state("domcontentloaded")
                time.sleep(5)
                
                for _ in range(3):
                    page.mouse.wheel(0, 1000)
                    time.sleep(1)

                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
                cards = soup.select('div[class*="car"], div[class*="item"], div[class*="result"], article, tr')
                
                encontrados = 0
                for card in cards:
                    texto = card.get_text(separator=" ", strip=True)
                    
                    # Verifica se qualquer uma das variações (ex: "rx7" ou "rx-7") está no texto
                    tem_modelo = any(v in texto.lower() for v in variacoes)
                    
                    if tem_modelo and len(texto) > 25:
                        link_tag = card.find('a', href=True)
                        link = '#'
                        if link_tag:
                            link = link_tag['href']
                            if not link.startswith('http'):
                                link = f"https://www.sbtjapan.com{link}"
                        
                        img_tag = card.find('img')
                        foto_url = ''
                        if img_tag:
                            foto_url = img_tag.get('src') or img_tag.get('data-src') or ''
                            if foto_url and not foto_url.startswith('http'):
                                foto_url = f"https://www.sbtjapan.com{foto_url}"

                        carro_dict = {
                            'stock_id': f"SBT-{termo}-{int(time.time())}-{len(lista_geral)}",
                            'carro': f"JDM {termo} (SBT)",
                            'ano_mes': '2000/1',
                            'preco': 'Sob Consulta',
                            'quilometragem': 'N/A',
                            'cambio': 'Manual',
                            'link': link,
                            'foto': foto_url
                        }
                        
                        if not any(c['link'] == link for c in lista_geral) and link != '#':
                            lista_geral.append(carro_dict)
                            encontrados += 1

                print(f"✅ Capturados {encontrados} anúncios para {termo}.")
                
            except Exception as e:
                print(f"❌ Erro ao processar o termo {termo}: {e}")

        browser.close()

    if lista_geral:
        salvar_no_banco(lista_geral)
    else:
        print("⚠️ Nenhum dado capturado no total.")

if __name__ == "__main__":
    raspar_sbt_japan()