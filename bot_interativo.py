import sqlite3
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

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

def inicializar_banco():
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_alerts (
            chat_id INTEGER,
            modelo TEXT,
            PRIMARY KEY (chat_id, modelo)
        )
    """)
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(marca, callback_data=f"marca_{marca}")] for marca in MARCAS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🚗 Escolha uma marca para ver os modelos disponíveis:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    dados = query.data
    chat_id = query.message.chat_id
    
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

    # ETAPA 1.5: Ativar/Desativar Alerta
    elif dados.startswith("alerta_"):
        partes = dados.split("_")
        marca_escolhida = partes[1]
        modelo_escolhido = partes[2]
        
        conn = sqlite3.connect('cars.db')
        cursor = conn.cursor()
        
        # Verifica se já tem alerta
        cursor.execute("SELECT * FROM user_alerts WHERE chat_id = ? AND modelo = ?", (chat_id, modelo_escolhido))
        existe = cursor.fetchone()
        
        if existe:
            cursor.execute("DELETE FROM user_alerts WHERE chat_id = ? AND modelo = ?", (chat_id, modelo_escolhido))
            status_texto = "❌ Alerta desativado para"
        else:
            cursor.execute("INSERT INTO user_alerts (chat_id, modelo) VALUES (?, ?)", (chat_id, modelo_escolhido))
            status_texto = "🔔 Alerta ativado com sucesso para"
            
        conn.commit()
        conn.close()
        
        await query.answer(f"{status_texto} {modelo_escolhido}!", show_alert=True)
        return

    # ETAPA 2: Escolher o Modelo (com paginação, fotos e botão de alerta)
    elif dados.startswith("modelo_"):
        partes = dados.split("_")
        marca_escolhida = partes[1]
        modelo_escolhido = partes[2]
        pagina = int(partes[3]) if len(partes) > 3 else 0
        
        modelo_limpo = modelo_escolhido.replace("-", "").replace(" ", "")
        
        conn = sqlite3.connect('cars.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT carro, ano_mes, preco, quilometragem, cambio, link, foto 
            FROM car_listings 
            WHERE carro LIKE ? OR REPLACE(REPLACE(carro, '-', ''), ' ', '') LIKE ?
        """, (f'%{modelo_escolhido}%', f'%{modelo_limpo}%'))
        anuncios = cursor.fetchall()
        
        # Checa se o usuário já tem alerta ativo para este modelo
        cursor.execute("SELECT * FROM user_alerts WHERE chat_id = ? AND modelo = ?", (chat_id, modelo_escolhido))
        alerta_ativo = cursor.fetchone()
        conn.close()

        # Se NÃO tiver carros
        if not anuncios:
            outros_modelos = [m for m in MODELOS_POR_MARCA.get(marca_escolhida, []) if m.lower() != modelo_escolhido.lower()]
            keyboard = []
            for alt in outros_modelos[:3]:
                keyboard.append([InlineKeyboardButton(f"Ver {alt}", callback_data=f"modelo_{marca_escolhida}_{alt}_0")])
            
            texto_alerta = "🔕 Desativar Alerta" if alerta_ativo else "🔔 Quero alerta de novos"
            keyboard.append([InlineKeyboardButton(f"{texto_alerta} {modelo_escolhido}", callback_data=f"alerta_{marca_escolhida}_{modelo_escolhido}")])
            keyboard.append([InlineKeyboardButton("🔄 Escolher Outra Marca", callback_data="voltar_marcas")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"😢 Que pena! No momento não temos unidades disponíveis do modelo *{modelo_escolhido}* ({marca_escolhida}).\n\n"
                f"Deseja ativar um alerta para ser avisado quando chegar novidade?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return

        # Paginação
        total_anuncios = len(anuncios)
        inicio = pagina * ITENS_POR_PAGINA
        fim = inicio + ITENS_POR_PAGINA
        anuncios_pagina = anuncios[inicio:fim]

        await query.message.delete()

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
                        chat_id=chat_id,
                        photo=foto,
                        caption=mensagem,
                        parse_mode='Markdown'
                    )
                    continue
                except Exception:
                    pass
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=mensagem,
                parse_mode='Markdown',
                disable_web_page_preview=False
            )

        # Botões de navegação e Alerta
        botoes_navegacao = []
        if pagina > 0:
            botoes_navegacao.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"modelo_{marca_escolhida}_{modelo_escolhido}_{pagina - 1}"))
        if fim < total_anuncios:
            botoes_navegacao.append(InlineKeyboardButton("Próximo ➡️", callback_data=f"modelo_{marca_escolhida}_{modelo_escolhido}_{pagina + 1}"))

        keyboard_final = []
        if botoes_navegacao:
            keyboard_final.append(botoes_navegacao)
        
        texto_alerta = "🔕 Desativar Alerta" if alerta_ativo else f"🔔 Ativar Alerta para {modelo_escolhido}"
        keyboard_final.append([InlineKeyboardButton(texto_alerta, callback_data=f"alerta_{marca_escolhida}_{modelo_escolhido}")])
        keyboard_final.append([InlineKeyboardButton("🔍 Escolher Outro Modelo", callback_data=f"marca_{marca_escolhida}")])
        keyboard_final.append([InlineKeyboardButton("🏠 Menu Principal (Marcas)", callback_data="voltar_marcas")])
        
        reply_markup_nav = InlineKeyboardMarkup(keyboard_final)

        await context.bot.send_message(
            chat_id=chat_id,
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

    inicializar_banco()

    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("🤖 Bot interativo com sistema de alertas rodando...")
    app.run_polling()