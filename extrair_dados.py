import json
import re

# 1. Abre o arquivo HTML bruto
with open("./data/carused_rx7.html", "r", encoding="utf-8") as file:
    html_content = file.read()

print("Buscando o padrão do JSON no arquivo...")

# 2. Vamos tentar capturar o texto que começa com as marcas que você viu
# Buscando algo que comece com os dados de modelos/marcas e termine de forma válida
# Esta regex procura a estrutura do JSON gigante que está no arquivo
match = re.search(re.escape('"model_categories"') + r'.*?\}\]\}\]\}(?=\s*<\/script>)', html_content)

# Se a regex acima for muito específica, vamos tentar uma busca por palavra-chave mais ampla
if not match:
    # Procura a tag script que contém o pedaço do texto que você postou
    # Vamos achar onde começa o "forklift" ou "suzuki" dentro de um <script>
    match = re.search(r'<script[^>]*>.*?forklift.*?<\/script>', html_content, re.DOTALL)

if match:
    print("Boa! Padrão de texto encontrado.")
    texto_script = match.group(0)
    
    # Vamos limpar as tags <script> </script> se elas vierem junto
    texto_json = re.sub(r'^<script[^>]*>', '', texto_script)
    texto_json = re.sub(r'</script>$', '', texto_json).strip()
    
    # Se o Next.js colocou o JSON direto, ele pode precisar de um ajuste para virar um dicionário válido
    # Vamos tentar decodificar. Se falhar, salvamos o texto puro para análise.
    try:
        # Se for um objeto JSON completo (começando com { e terminando com })
        if texto_json.startswith('{') and texto_json.endswith('}'):
            dados = json.loads(texto_json)
        else:
            # Se for uma atribuição tipo: window.__NEXT_DATA__ = {...}
            # Vamos tentar isolar apenas o que está entre as chaves principais
            inicio_chave = texto_json.find('{')
            fim_chave = texto_json.rfind('}') + 1
            dados = json.loads(texto_json[inicio_chave:fim_chave])
            
        with open("./data/dados_formatados.json", "w", encoding="utf-8") as json_file:
            json.dump(dados, json_file, indent=4, ensure_ascii=False)
        print("Sucesso! Arquivo 'dados_formatados.json' gerado com sucesso.")
        
    except json.JSONDecodeError as e:
        print(f"Opa, o texto foi extraído, mas não é um JSON 100% puro para o Python converter diretamente: {e}")
        print("Salvando o texto extraído puramente em 'dados_brutos.txt' para darmos uma olhada.")
        with open("./data/dados_brutos.txt", "w", encoding="utf-8") as txt_file:
            txt_file.write(texto_json)
else:
    print("Ainda não consegui isolar o bloco. Vamos tentar uma última linha de defesa.")