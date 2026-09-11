import os
import pandas as pd
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Función auxiliar para leer la planilla de manera segura (.xls o .xlsx)
def obtener_datos_excel():
    excel_path = "Menu y Promos Comercio.xls"
    if not os.path.exists(excel_path):
        excel_path = "Menu y Promos Comercio.xlsx"
    
    try:
        df_menu = pd.read_excel(excel_path, sheet_name="Menu y Productos")
        df_promos = pd.read_excel(excel_path, sheet_name="Promociones y Combos")
        return df_menu, df_promos
    except Exception as e:
        return None, None

@app.route("/bot", methods=["POST"])
def bot_whatsapp():
    incoming_msg = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    # 1. Activación con el saludo "hola" o similar
    if any(word in incoming_msg for word in ["hola", "buenas", "menu", "empezar", "comenzar", "pedir"]):
        welcome_text = (
            "¡Hola! Te damos la bienvenida a *Pizzería Pedidos y Delivery* 🍕👋\n\n"
            "¿Qué consulta deseás realizar hoy?\n\n"
            "Por favor, respondé con el número de la opción:\n"
            "1️⃣ Ver catálogo completo\n"
            "2️⃣ Consultar por algún producto por código\n"
            "3️⃣ Consultar promos o combos"
        )
        msg.body(welcome_text)
    
    # 2. Opción 1: Ver catálogo completo
    elif incoming_msg == "1":
        df_menu, _ = obtener_datos_excel()
        if df_menu is not None:
            catalogo_resumen = "📋 *Catálogo Completo - Pizzería Pedidos y Delivery* 🍕\n\n"
            for index, row in df_menu.head(15).iterrows():
                catalogo_resumen += f"• *{row['Codigo']}* - {row['Producto/ Variedad']}: ${row['Precio ($)']}\n"
            catalogo_resumen += "\n*(Mostrando los principales productos).* "
            msg.body(catalogo_resumen)
        else:
            msg.body("📋 *Catálogo Completo*\n\nEstamos actualizando nuestra base de datos de productos. ¡En instantes te enviamos el detalle!")

    # 3. Opción 2: Consultar por algún producto por código
    elif incoming_msg == "2":
        msg.body(
            "🔍 *Consulta por Producto por Código*\n\n"
            "Por favor, escribí el código exacto del producto que buscás (por ejemplo: `P01`, `E01`, `S01`) para ver su precio y descripción."
        )

    # 4. Opción 3: Consultar promos o combos
    elif incoming_msg == "3":
        _, df_promos = obtener_datos_excel()
        if df_promos is not None:
            promos_resumen = "🔥 *Consultas de Promos y Combos* 🍕🍻\n\n"
            for index, row in df_promos.iterrows():
                promos_resumen += f"• *{row['Codigo']}* - *{row['Producto/ Variedad']}*\n  _{row['Descripción/Ingredientes']}_\n  Precio: *${row['Precio ($)']}*\n\n"
            msg.body(promos_resumen)
        else:
            msg.body("🔥 *Promos y Combos*\n\nConsultá nuestras ofertas especiales actualizadas.")
    
    else:
        # Respuesta por defecto si escriben un código o cualquier otra cosa
        msg.body(
            f"Recibimos tu consulta: \"{incoming_msg}\".\n"
            "Para ver las opciones principales nuevamente, escribí **'Hola'**."
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False) 
