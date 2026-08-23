import sqlite3
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
token = os.getenv("TELEGRAM_TOKEN")

MARCAS = ["Mazda", "Toyota", "Nissan", "Subaru", "Mitsubishi"]

MODELOS_POR_MARCA = {
    "Nissan": ["Silvia", "GT-R", "Skyline", "Fairlady Z"],
    "Toyota": ["Supra", "AE86", "Chaser", "Soarer"],
    "Mazda": ["RX-7", "RX-8"],
    "Subaru": ["Impreza", "BRZ", "WRX"],
    "Mitsubishi": ["Lancer", "GTO"]
}

ITENS_POR_PAGINA = 3

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(marca, callback_data=f"marca_{marca}")] for marca in MARCAS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🚗 Escolha uma marca para ver os modelos disponíveis:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    dados = query.data
    
    # ETAPA 1: Escolher a Marca
    if dados.startswith("marca_"):
        marca_escolhida = dados.split("_")[1]
        modelos = MODELOS_POR_MARCA.get(marca_escolhida, [])
        
        keyboard = []
        for modelo in modelos:
            keyboard.append([InlineKeyboardButton(modelo, callback_data=f"modelo_{marca_escolhida}_{modelo}_0")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Voltar para Marcas", callback_data="voltar_marcas")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(f"🔍 Escolha o modelo da marca *{marca_escolhida}*:", reply_markup=reply_markup, parse_mode='Markdown')

    # ETAPA 2: Escolher o Modelo (com paginação, fotos e links corrigidos)
    elif dados.startswith("modelo_"):
        partes = dados.split("_")
        marca_escolhida = partes[1]
        modelo_escolhido = partes[2]
        pagina = int(partes[3]) if len(partes) > 3 else 0
        
        # Limpa o modelo para garantir que busca sem conflito de hífen
        modelo_limpo = modelo_escolhido.replace("-", "").replace(" ", "")
        
        conn = sqlite3.connect('cars.db')
        cursor = conn.cursor()
        
        # Busca focada no modelo e variações (com e sem hífen), ignorando a obrigatoriedade da marca escrita na string
        cursor.execute("""
            SELECT carro, ano_mes, preco, quilometragem, cambio, link, foto 
            FROM car_listings 
            WHERE carro LIKE ? OR REPLACE(REPLACE(carro, '-', ''), ' ', '') LIKE ?
        """, (f'%{modelo_escolhido}%', f'%{modelo_limpo}%'))
        anuncios = cursor.fetchall()
        conn.close()
        # Se NÃO tiver carros
        if not anuncios:
            outros_modelos = [m for m in MODELOS_POR_MARCA.get(marca_escolhida, []) if m.lower() != modelo_escolhido.lower()]
            keyboard = []
            for alt in outros_modelos[:3]:
                keyboard.append([InlineKeyboardButton(f"Ver {alt}", callback_data=f"modelo_{marca_escolhida}_{alt}_0")])
            
            keyboard.append([InlineKeyboardButton("🔄 Escolher Outra Marca", callback_data="voltar_marcas")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"😢 Que pena! No momento não temos unidades disponíveis do modelo *{modelo_escolhido}* ({marca_escolhida}).\n\n"
                f"Que tal escolher outro modelo da mesma marca ou trocar de marca?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return

        # Paginação
        total_anuncios = len(anuncios)
        inicio = pagina * ITENS_POR_PAGINA
        fim = inicio + ITENS_POR_PAGINA
        anuncios_pagina = anuncios[inicio:fim]

        # Apaga a mensagem anterior do menu
        await query.message.delete()

        # Envia os carros da página atual com Foto e Link Clicável formatado corretamente
        for carro, ano, preco, km, cambio, link, foto in anuncios_pagina:
            mensagem = (
                f"🔥 *{carro}*\n"
                f"📅 Ano/Mês: {ano}\n"
                f"💰 Preço: {preco}\n"
                f"🛣️ Quilometragem: {km}\n"
                f"⚙️ Câmbio: {cambio}\n\n"
                f"🔗 [Clique aqui para ver o anúncio completo]({link})"
            )
            
            if foto and foto.startswith('http'):
                try:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=foto,
                        caption=mensagem,
                        parse_mode='Markdown'
                    )
                    continue
                except Exception:
                    pass
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=mensagem,
                parse_mode='Markdown',
                disable_web_page_preview=False
            )

        # Botões de navegação
        botoes_navegacao = []
        if pagina > 0:
            botoes_navegacao.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"modelo_{marca_escolhida}_{modelo_escolhido}_{pagina - 1}"))
        if fim < total_anuncios:
            botoes_navegacao.append(InlineKeyboardButton("Próximo ➡️", callback_data=f"modelo_{marca_escolhida}_{modelo_escolhido}_{pagina + 1}"))

        keyboard_final = []
        if botoes_navegacao:
            keyboard_final.append(botoes_navegacao)
        
        keyboard_final.append([InlineKeyboardButton("🔍 Escolher Outro Modelo", callback_data=f"marca_{marca_escolhida}")])
        keyboard_final.append([InlineKeyboardButton("🏠 Menu Principal (Marcas)", callback_data="voltar_marcas")])
        
        reply_markup_nav = InlineKeyboardMarkup(keyboard_final)

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"📄 Página {pagina + 1} de {(total_anuncios + ITENS_POR_PAGINA - 1) // ITENS_POR_PAGINA} para *{modelo_escolhido}*:",
            reply_markup=reply_markup_nav,
            parse_mode='Markdown'
        )

    elif dados == "voltar_marcas":
        keyboard = [[InlineKeyboardButton(marca, callback_data=f"marca_{marca}")] for marca in MARCAS]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🚗 Escolha uma marca para começar:", reply_markup=reply_markup)

if __name__ == '__main__':
    if not token:
        print("❌ Erro: TELEGRAM_TOKEN não encontrado no arquivo .env!")
        exit(1)

    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("🤖 Bot interativo atualizado e seguro rodando...")
    app.run_polling()