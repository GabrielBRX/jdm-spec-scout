import asyncio
from telegram import Bot

TOKEN = '8941953034:AAHQGWXYTQtpDSysVE_JNL6zq-D1JJIjT78'

async def pegar_chat_id():
    bot = Bot(token=TOKEN)
    
    updates = await bot.get_updates()
    
    if not updates:
        print("⚠️ Nenhuma mensagem encontrada. Mande uma mensagem para o seu bot no Telegram primeiro!")
        return

    
    chat_id = updates[0].effective_chat.id
    print(f"🎉 Seu CHAT_ID é: {chat_id}")

if __name__ == '__main__':
    asyncio.run(pegar_chat_id())




    