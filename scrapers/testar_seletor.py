from bs4 import BeautifulSoup

with open("scrapers/carused_dump.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

print("🔍 --- GARIMPANDO LINKS DOS CARDS DE CARROS ---")
links = soup.find_all("a")
links_filtrados = 0

for link in links:
    href = link.get("href", "")
    texto = link.get_text(strip=True, separator=" ")
    
    # Ignora a página inicial e os links repetitivos do menu de marcas/categorias
    if href and "/pt" in href and not href.endswith("/pt") and "car-list" not in href:
        links_filtrados += 1
        print(f"Link {links_filtrados}: href='{href}' | texto='{texto[:70]}'")

if links_filtrados == 0:
    print("\n❌ Nenhum link fora do menu foi encontrado. Vamos checar se existem botões ou divs com IDs de estoque:")
    # Caso os cards não sejam tags <a> diretas, vamos caçar qualquer texto que pareça o preço ou ID
    for div in soup.find_all(["div", "p"]):
        txt = div.get_text(strip=True)
        if "$" in txt or "REF" in txt:
            print(f"Trecho encontrado: {txt[:100]}")