import requests
from bs4 import BeautifulSoup


API_URL = "http://127.0.0.1:8000/cars"

def simular_garimpo_leilao():
    print("🤖 [Robô]: Iniciando varredura na web...")

    URL_ALVO = "https://scrapepark.org/courses/spanish/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        print(f"🌐 [Robô]: Conectando ao site: {URL_ALVO}")
        resposta = requests.get(URL_ALVO, headers=headers)

        if resposta.status_code == 200:
            print("✅ [Robô]: Conexão bem-sucedida! HTML capturado.")
            html_real = resposta.text
            soup = BeautifulSoup(html_real, "html.parser")
        else:
            print(f"❌ [Robô]: Erro ao acessar o site. Status: {resposta.status_code}")
            return
    except Exception as e:
        print(f"💥 [Robô]: Falha catastrófica de conexão: {e}")
        return

    carros_raspados = []

    
    cards_produtos = soup.find_all("div", class_="col-lg-4")

    print(f"📦 [Robô]: Encontrei {len(cards_produtos)} produtos na página. Iniciando extração...")

    for card in cards_produtos:
        try:
            
            nome_tag = card.find("h5")
            if not nome_tag:
                continue
            nome_produto = nome_tag.text.strip()
            
            
            preco_tag = card.find("h<h6>" if card.find("h6") else "h6") 
            preco_tag = card.find("h6")
            
            if preco_tag:
                preco_texto = preco_tag.text.strip()
            else:
                preco_texto = "0"
                
            
            preco_limpo = "".join(filter(str.isdigit, preco_texto))
            preco_final = int(preco_limpo) if preco_limpo else 0

            
            item_formatado = {
                "model": f"JDM Teste - {nome_produto}",  
                "auction_grade": "Grade 4.5",
                "mileage": 50000,
                "price_jpy": preco_final,  
                "transmission": "Manual",
                "url": f"https://leilaoteste.com/{nome_produto.lower().replace(' ', '-')}"
            }
            
            carros_raspados.append(item_formatado)
            print(f"✔️ Extraído com sucesso: {nome_produto} | Preço: {preco_final}")
            
        except Exception as erro_no_card:
            print(f"⚠️ Falha ao processar card: {erro_no_card}")
            continue

    print(f"\n🚀 [Robô]: Total de itens extraídos com sucesso: {len(carros_raspados)}")

    
    for carro in carros_raspados:
        print(f"\n🔍 [Robô]: Analisando {carro['model']} - URL: {carro['url']}")
        
        check_response = requests.get(f"{API_URL}/check-url/", params={"url": carro["url"]})
        
        if check_response.status_code == 404:
            print("🆕 [Robô]: Item novo detectado! Enviando para a API (POST)...")
            create_response = requests.post(f"{API_URL}/", json=carro)
            if create_response.status_code == 200:
                print(f"✅ [Robô]: Sucesso! Cadastrado com ID {create_response.json()['id']}")
            else:
                print(f"❌ [Robô]: Erro ao cadastrar. Status: {create_response.status_code}")
                
        elif check_response.status_code == 200:
            carro_no_banco = check_response.json()
            id_do_carro = carro_no_banco["id"]
            preco_antigo = carro_no_banco["price_jpy"]
            
            print(f"⚠️ [Robô]: Este item já está no banco (ID {id_do_carro}). Verificando preço...")
            
            if preco_antigo != carro["price_jpy"]:
                print(f"📉 [Robô]: Preço mudou de {preco_antigo} para {carro['price_jpy']}! Atualizando (PUT)...")
                update_response = requests.put(f"{API_URL}/{id_do_carro}", json=carro)
                if update_response.status_code == 200:
                    print(f"🔄 [Robô]: Sucesso! Preço atualizado para o ID {id_do_carro}.")
            else:
                print("😴 [Robô]: O preço continua o mesmo.")

if __name__ == "__main__":
    simular_garimpo_leilao()