import requests

# URL base da sua API
API_URL = "http://127.0.0.1:8000/cars"

def simular_garimpo_leilao():
    print("🤖 [Robô]: Iniciando varredura nos sites de leilão do Japão...")

    # Dois carros simulados
    carros_raspados = [
        {
            "model": "RX-7 Spirit R",
            "auction_grade": "Grade 4.5",
            "mileage": 42000,
            "price_jpy": 8500000,
            "transmission": "Manual",
            "url": "https://leilaojapao.com/rx7-spirit-r-42k"
        },
        {
            "model": "RX-7 Standard",
            "auction_grade": "Grade 4",
            "mileage": 180000,
            "price_jpy": 4300000,
            "transmission": "Manual",
            "url": "https://linkfalso123.com"
        }
    ]

    for carro in list(carros_raspados):
        print(f"\n🔍 [Robô]: Analisando {carro['model']} - URL: {carro['url']}")
        
        # Pergunta para a API se essa URL já existe (Atenção: verifique se no seu main.py a rota é 'check-url/')
        check_response = requests.get(f"{API_URL}/check-url/", params={"url": carro["url"]})
        
        if check_response.status_code == 404:
            print("🆕 [Robô]: Carro novo detectado! Enviando comando de cadastro (POST)...")
            create_response = requests.post(f"{API_URL}/", json=carro)
            if create_response.status_code == 200:
                print(f"✅ [Robô]: Sucesso! Carro cadastrado com ID {create_response.json()['id']}")
            else:
                print(f"❌ [Robô]: Erro ao cadastrar. Status: {create_response.status_code}")
                
        elif check_response.status_code == 200:
            carro_no_banco = check_response.json()
            id_do_carro = carro_no_banco["id"]
            preco_antigo = carro_no_banco["price_jpy"]
            
            print(f"⚠️ [Robô]: Este carro já está no banco (ID {id_do_carro}). Verificando preço...")
            
            if preco_antigo != carro["price_jpy"]:
                print(f"📉 [Robô]: Preço mudou! Atualizando (PUT)...")
                update_response = requests.put(f"{API_URL}/{id_do_carro}", json=carro)
                if update_response.status_code == 200:
                    print(f"🔄 [Robô]: Sucesso! Preço atualizado para o ID {id_do_carro}.")
            else:
                print("😴 [Robô]: O preço continua o mesmo.")

if __name__ == "__main__":
    simular_garimpo_leilao()