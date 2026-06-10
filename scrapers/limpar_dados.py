import json
import re
from pathlib import Path

def extrair_detalhes(texto):
    """Usa Regex para extrair dados limpos do blocão do anúncio."""
    # Extrai o Ano/Mês e o Modelo
    ano_match = re.search(r"(\d{4}/\d{1,2})\s+MAZDA\s+RX7", texto, re.IGNORECASE)
    ano_modelo = ano_match.group(1) if ano_match else "N/A"
    
    # Extrai o preço em USD (pega o primeiro valor numérico após USD)
    preco_match = re.search(r"USD\s*([\d,]+)", texto)
    preco = f"USD {preco_match.group(1)}" if preco_match else "Sob Consulta"
    
    # Extrai o ID do Estoque
    stock_match = re.search(r"Stock Id:\s*\n*\s*([A-Z0-9]+)", texto)
    stock_id = stock_match.group(1).strip() if stock_match else "N/A"
    
    # Extrai a Localização no Japão
    loc_match = re.search(r"Inventory location\s*:\s*\n*\s*([A-Za-z]+,\s*[A-Za-z]+)", texto)
    localizacao = loc_match.group(1).strip() if loc_match else "Japão"
    
    # Extrai Quilometragem (ex: 109,700km)
    km_match = re.search(r"(\d[\d,]*\s*km)", texto, re.IGNORECASE)
    km = km_match.group(1) if km_match else "N/A"
    
    # Extrai Câmbio (MT ou AT)
    cambio_match = re.search(r"\b(MT|AT)\b", texto)
    cambio = "Manual (MT)" if cambio_match and cambio_match.group(1) == "MT" else "Automático (AT)" if cambio_match else "N/A"
    
    # Extrai a Cor
    cores_possiveis = ["WHITE", "RED", "BLUE", "BLACK", "SILVER", "GREY", "YELLOW"]
    cor = "N/A"
    for c in cores_possiveis:
        if c in texto:
            cor = c.capitalize()
            break

    return {
        "carro": "Mazda RX-7",
        "ano_mes": ano_modelo,
        "preco": preco,
        "quilometragem": km,
        "cambio": cambio,
        "cor": cor,
        "localizacao": localizacao,
        "stock_id": stock_id
    }

def processar_json_bruto():
    print("🧹 [jdm-spec-scout]: Iniciando a limpeza pesada dos dados...")
    
    # Lógica de caminho inteligente usando Pathlib
    caminho_atual = Path(__file__).resolve().parent
    pasta_data = caminho_atual.parent / "data"
    
    caminho_bruto = pasta_data / "resultados_finais_rx7.json"
    caminho_limpo = pasta_data / "carros_estoque_limpo.json"

    try:
        with open(caminho_bruto, "r", encoding="utf-8") as f:
            dados_brutos = json.load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado em: {caminho_bruto}")
        print("Certifique-se de que moveu os arquivos para a pasta 'data'.")
        return

    carros_limpos = []
    
    for item in dados_brutos:
        texto_completo = item.get("modelo", "") + " " + item.get("dados_gerais", "")
        
        if "MAZDA RX7" in texto_completo.upper() and ("USD" in texto_completo or "FD3S" in texto_completo):
            carro_tratado = extrair_detalhes(texto_completo)
            carros_limpos.append(carro_tratado)
            
    vistos = set()
    carros_unicos = []
    for c in list(carros_limpos):
        if c["stock_id"] not in vistos:
            vistos.add(c["stock_id"])
            carros_unicos.append(c)

    with open(caminho_limpo, "w", encoding="utf-8") as f:
        json.dump(carros_unicos, f, indent=4, ensure_ascii=False)
        
    print(f"✨ Sucesso! Dados salvos em: {caminho_limpo}")

if __name__ == "__main__":
    processar_json_bruto()