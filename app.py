import os
import pandas as pd
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

EXCEL_FILE = "Menu y Promos Comercio.xlsx"

@app.route('/bot', methods=["POST"])
def bot_whatsapp():
    incoming_msg = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    if any(word in incoming_msg for word in ["hola", "menu", "empezar", "buenas", "inicio", "pedir"]):
        welcome_text = (
            "¡Hola! Te damos la bienvenida a Pizzería Pedidos y Delivery. 🍕\n\n"
            "¿Qué consulta deseás realizar hoy? Por favor, elegí una opción:\n"
            "1️⃣ Ver Catálogo Completo (Pizzas y Empanadas)\n"
            "2️⃣ Consulta por algún Producto por Código\n"
            "3️⃣ Consulta por Promos y Combos\n\n"
            "Respondé con el número de la opción que prefieras."
        )
        msg.body(welcome_text)
        
    elif "1" in incoming_msg:
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name='Menu y Productos')
            catalogo_texto = "📄 *Nuestras Pizzas y Empanadas:*\n\n"
            
            # Limitamos a mostrar una cantidad segura para que WhatsApp no rechace el mensaje
            for index, row in df.head(15).iterrows():
                codigo = row.get('Codigo', '')
                producto = row.get('Producto/ Variedad', '')
                precio = row.get('Precio ($)', '')
                catalogo_texto += f"▪️ [{codigo}] {producto} - ${precio}\n"
                
            catalogo_texto += "\n(Escribí el número 2 y el código para consultar detalles)"
            msg.body(catalogo_texto)
        except Exception as e:
            msg.body("Hubo un error al leer el archivo de productos.")
        
    elif "2" in incoming_msg:
        msg.body("Por favor, ingresa el código exacto del producto que deseas consultar (ej: P01 o E01).")
        
    elif "3" in incoming_msg:
        try:
            df_promos = pd.read_excel(EXCEL_FILE, sheet_name='Promociones y Combos')
            promos_texto = "🎉 *Promos y Combos Vigentes:*\n\n"
            
            for index, row in df_promos.iterrows():
                codigo = row.get('Codigo', '')
                nombre = row.get('Producto/ Variedad', '')
                precio = row.get('Precio ($)', '')
                promos_texto += f"🎁 [{codigo}] {nombre} - ${precio}\n"
                
            msg.body(promos_texto)
        except Exception as e:
            msg.body("Hubo un error al leer las promos.")
        
    else:
        msg.body("No reconocí tu mensaje. Escribí 'hola' para ver el menú principal.")

    return str(resp)

if __name__ == "__main__":
    app.run() 
