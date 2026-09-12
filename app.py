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
            "¿Qué deseas ver hoy? Elegí una opción:\n"
            "1️⃣ Pizzas 🍕\n"
            "2️⃣ Empanadas 🥟\n"
            "3️⃣ Promos y Combos 🎉\n\n"
            "💡 También podés escribir directamente el código de un producto (ej: P14 o E01) para ver sus ingredientes y precio."
        )
        msg.body(welcome_text)
        
    elif incoming_msg_lower in ["1", "pizzas"]:
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name='Menu y Productos')
            pizzas = df[df['Categoria'].astype(str).str.strip().str.lower() == 'pizzas']
            
            texto = "🍕 *LISTA DE PIZZAS:*\n\n"
            for _, row in pizzas.iterrows():
                codigo = str(row.get('Codigo', '')).strip()
                producto = str(row.get('Producto/ Variedad', '')).strip()
                precio = str(row.get('Precio ($)', '')).strip()
                if codigo and codigo != 'nan':
                    texto += f"▪️ [{codigo}] {producto} - ${precio}\n"
                    
            texto += "\n*(Escribí el código para ver ingredientes o 'hola' para volver al menú)*"
            msg.body(texto)
        except Exception as e:
            msg.body(f"Error en Pizzas: {str(e)}")
        
    elif incoming_msg_lower in ["2", "empanadas"]:
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name='Menu y Productos')
            empanadas = df[df['Categoria'].astype(str).str.strip().str.lower() == 'empanadas']
            
            texto = "🥟 *LISTA DE EMPANADAS:*\n\n"
            for _, row in empanadas.iterrows():
                codigo = str(row.get('Codigo', '')).strip()
                producto = str(row.get('Producto/ Variedad', '')).strip()
                precio = str(row.get('Precio ($)', '')).strip()
                if codigo and codigo != 'nan':
                    texto += f"▪️ [{codigo}] {producto} - ${precio}\n"
                    
            texto += "\n*(Escribí el código para ver ingredientes o 'hola' para volver al menú)*"
            msg.body(texto)
        except Exception as e:
            msg.body(f"Error en Empanadas: {str(e)}")
        
    elif incoming_msg_lower in ["3", "promos", "combos"]:
        try:
            df_promos = pd.read_excel(EXCEL_FILE, sheet_name='Promociones y Combos')
            promos_texto = "🎉 *Promos y Combos Vigentes:*\n\n"
            
            for _, row in df_promos.iterrows():
                codigo = str(row.get('Codigo', '')).strip()
                nombre = str(row.get('Producto/ Variedad', '')).strip()
                precio = str(row.get('Precio ($)', '')).strip()
                if codigo and codigo != 'nan':
                    promos_texto += f"🎁 [{codigo}] {nombre} - ${precio}\n"
                    
            promos_texto += "\n*(Escribí 'hola' para volver al menú principal)*"
            msg.body(promos_texto)
        except Exception as e:
            msg.body(f"Error en Promos: {str(e)}")
        
    else:
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
                    f"▪️ *Precio:* ${precio}\n\n"
                    f"*(Escribí 'hola' para volver al menú principal)*"
                )
                msg.body(detalle_texto)
            else:
                msg.body("No reconocí tu mensaje. Escribí 'hola' para ver el menú principal.")
        except Exception as e:
            msg.body("No reconocí tu mensaje. Escribí 'hola' para ver el menú principal.")

    return str(resp)

if __name__ == "__main__":
    app.run() 
