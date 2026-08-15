import subprocess

def rodar_atualizacao():
    print("🚀 [JDM Scout] Iniciando a atualização dos catálogos...")
    
    # 1. Roda o scraper do Carused (se houver o arquivo configurado)
    try:
        print("📥 Atualizando dados do Carused...")
        subprocess.run(["python", "scrapers/baixar_carused.py"], check=True)
    except Exception as e:
        print(f"⚠️ Erro ao atualizar Carused: {e}")

    # 2. Roda o scraper do SBT Japan
    try:
        print("📥 Atualizando dados do SBT Japan...")
        subprocess.run(["python", "scrapers/sbtjapan_scraper.py"], check=True)
    except Exception as e:
        print(f"⚠️ Erro ao atualizar SBT Japan: {e}")

    print("✅ Atualização concluída! O banco de dados cars.db está pronto.")

if __name__ == "__main__":
    rodar_atualizacao()