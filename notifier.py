import sqlite3
import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

# Carrega as variáveis do arquivo .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_PATH = 'cars.db'

async def verificar_e_notificar():
    if not TOKEN or not CHAT_ID:
        print("❌ Erro: Token ou Chat ID do Telegram não configurados nas variáveis de ambiente.")
        return

    bot = Bot(token=TOKEN)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT carro, preco, quilometragem, link FROM car_listings ORDER BY id DESC LIMIT 10")
    carros = cursor.fetchall()
    conn.close()

    if not carros:
        print("Nenhum carro encontrado no banco.")
        return

    mensagem = "🚗 *Novas Ofertas Encontradas:*\n\n"
    contador = 0

    for carro in carros:
        nome, preco, km, link = carro
        link_limpo = link.strip() if link else "https://carused.jp"

        mensagem += f"*{nome}*\n"
        mensagem += f"💰 Preço: {preco}\n"
        mensagem += f"🏃 KM: {km}\n"
        mensagem += f"🔗 [Ver no site]({link_limpo})\n\n"
        contador += 1

    if contador > 0:
        await bot.send_message(
            chat_id=CHAT_ID, 
            text=mensagem, 
            parse_mode='Markdown'
        )
        print(f"✨ Notificação enviada com {contador} carros!")

if __name__ == '__main__':
    asyncio.run(verificar_e_notificar())