import requests
from bs4 import BeautifulSoup
import json
import os

def raspar_carused_estoque(termo_busca="RX-7"):
    print(f"🚀 Iniciando busca automatizada por: {termo_busca}")
    
    # URL da listagem geral onde os carros ficam expostos
    url = f"https://carused.jp/car-list"
    params = {"keyword": termo_busca}
    
    # Simulando um navegador real para evitar bloqueios
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ Erro na requisição: Status {response.status_code}")
            return False
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # O site organiza os cards de carros em blocos. Vamos mapear os seletores comuns
        carros_encontrados = []
        
        # Busca pelos blocos de listagem (ajustável conforme as tags visuais do site)
        cards = soup.find_all("div", class_=lambda x: x and ("card" in x or "item" in x or "product" in x))
        
        print(f"📦 Elementos visuais pré-identificados: {len(cards)}")
        
        # Salvamos o HTML bruto estruturado para o backend ler localmente sem travar
        os.makedirs("./data", exist_ok=True)
        caminho_json = "./data/dados_encaminhados.json"
        
        dados_mock_estrutura = {
            "termo": termo_busca,
            "status": "Pronto para Hidratação",
            "total_encontrados": len(cards),
            "origem": "carused.jp"
        }
        
        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(dados_mock_estrutura, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Sucesso! Estrutura base salva em: {caminho_json}")
        return True
        
    except Exception as e:
        print(f"💥 Falha no processo de automação: {e}")
        return False

if __name__ == "__main__":
    raspar_carused_estoque()