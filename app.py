import os
import pandas as pd
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

EXCEL_FILE = "Menu y Promos Comercio.xlsx"

@app.route('/bot', methods=["POST"])
def bot_whatsapp():
    incoming_msg = request.values.get('Body', '').strip()
    incoming_msg_lower = incoming_msg.lower()
    resp = MessagingResponse()
    msg = resp.message()

    if any(word in incoming_msg_lower for word in ["hola", "menu", "empezar", "buenas", "inicio", "pedir"]):
        welcome_text = (
            "¡Hola! Te damos la bienvenida a Pizzería Pedidos y Delivery. 🍕\n\n"
            "¿Qué consulta deseás realizar hoy? Por favor, elegí una opción:\n"
            "1️⃣ Ver Catálogo Completo (Pizzas y Empanadas)\n"
            "2️⃣ Consulta por código (ej: escribí P14 o E01 directamente)\n"
            "3️⃣ Consulta por Promos y Combos\n\n"
            "Respondé con el número de la opción o el código del producto."
        )
        msg.body(welcome_text)
        
    elif incoming_msg_lower == "1" or "catálogo" in incoming_msg_lower:
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name='Menu y Productos')
            catalogo_texto = "📄 *Nuestras Pizzas y Empanadas:*\n\n"
            
            for index, row in df.head(15).iterrows():
                codigo = str(row.get('Codigo', '')).strip()
                producto = row.get('Producto/ Variedad', '')
                precio = row.get('Precio ($)', '')
                catalogo_texto += f"▪️ [{codigo}] {producto} - ${precio}\n"
                
            catalogo_texto += "\n(Escribí directamente el código, ej: P14, para ver los ingredientes)"
            msg.body(catalogo_texto)
        except Exception as e:
            msg.body("Hubo un error al leer el archivo de productos.")
        
    elif incoming_msg_lower == "3" or "promos" in incoming_msg_lower:
        try:
            df_promos = pd.read_excel(EXCEL_FILE, sheet_name='Promociones y Combos')
            promos_texto = "🎉 *Promos y Combos Vigentes:*\n\n"
            
            for index, row in df_promos.iterrows():
                codigo = str(row.get('Codigo', '')).strip()
                nombre = row.get('Producto/ Variedad', '')
                precio = row.get('Precio ($)', '')
                promos_texto += f"🎁 [{codigo}] {nombre} - ${precio}\n"
                
            msg.body(promos_texto)
        except Exception as e:
            msg.body("Hubo un error al leer las promos.")
        
    else:
        # Búsqueda por código de producto en el Excel
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name='Menu y Productos')
            # Busca si el código escrito coincide con alguna fila (sin importar mayúsculas/minúsculas)
            resultado = df[df['Codigo'].astype(str).str.strip().str.lower() == incoming_msg_lower]
            
            if not resultado.empty:
                row = resultado.iloc[0]
                codigo = row.get('Codigo', '')
                producto = row.get('Producto/ Variedad', '')
                descripcion = row.get('Descripción/Ingredientes', '')
                precio = row.get('Precio ($)', '')
                
                detalle_texto = (
                    f"🍕 *Producto Encontrado:*\n\n"
                    f"▪️ *Código:* {codigo}\n"
                    f"▪️ *Variedad:* {producto}\n"
                    f"▪️ *Ingredientes:* {descripcion}\n"
                    f"▪️ *Precio:* ${precio}"
                )
                msg.body(detalle_texto)
            else:
                msg.body("No reconocí el código ingresado. Escribí 'hola' para ver el menú principal o probá con otro código (ej: P01).")
        except Exception as e:
            msg.body("No reconocí tu mensaje. Escribí 'hola' para ver el menú principal.")

    return str(resp)

if __name__ == "__main__":
    app.run() 
