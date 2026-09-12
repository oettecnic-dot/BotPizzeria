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
            "1️⃣ Ver Catálogo Completo\n"
            "2️⃣ Consulta por código (escribí el código directamente, ej: P14)\n"
            "3️⃣ Consulta por Promos y Combos\n\n"
            "Respondé con el número de la opción o el código del producto."
        )
        msg.body(welcome_text)
        
    elif incoming_msg_lower == "1" or "catálogo" in incoming_msg_lower:
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name='Menu y Productos')
            catalogo_texto = "📄 *Catálogo Completo:*\n"
            
            categoria_actual = ""
            for _, row in df.iterrows():
                codigo = str(row.get('Codigo', '')).strip()
                categoria = str(row.get('Categoria', '')).strip()
                producto = str(row.get('Producto/ Variedad', '')).strip()
                precio = str(row.get('Precio ($)', '')).strip()
                
                if codigo and codigo != 'nan' and producto != 'nan':
                    if categoria != categoria_actual:
                        categoria_actual = categoria
                        catalogo_texto += f"\n*{categoria_actual.upper()}*\n"
                    catalogo_texto += f"▪️ [{codigo}] {producto} - ${precio}\n"
                
            catalogo_texto += "\n*(Escribí el código, ej: P14, para ver ingredientes)*"
            msg.body(catalogo_texto)
        except Exception as e:
            msg.body("Hubo un error al leer el archivo de productos.")
        
    elif incoming_msg_lower == "3" or "promos" in incoming_msg_lower:
        try:
            df_promos = pd.read_excel(EXCEL_FILE, sheet_name='Promociones y Combos')
            promos_texto = "🎉 *Promos y Combos Vigentes:*\n\n"
            
            for index, row in df_promos.iterrows():
                codigo = str(row.get('Codigo', '')).strip()
                nombre = str(row.get('Producto/ Variedad', '')).strip()
                precio = str(row.get('Precio ($)', '')).strip()
                if codigo and codigo != 'nan':
                    promos_texto += f"🎁 [{codigo}] {nombre} - ${precio}\n"
                
            msg.body(promos_texto)
        except Exception as e:
            msg.body("Hubo un error al leer las promos.")
        
    else:
        # Búsqueda por código de producto en el Excel
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name='Menu y Productos')
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
                msg.body("No reconocí el código ingresado. Escribí 'hola' para ver el menú principal.")
        except Exception as e:
            msg.body("No reconocí tu mensaje. Escribí 'hola' para ver el menú principal.")

    return str(resp)

if __name__ == "__main__":
    app.run() 
