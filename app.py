import os
import pandas as pd
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Cargar el archivo de Excel del catálogo
EXCEL_FILE = "Menu y Promos Comercio.xlsx"

@app.route('/bot', methods=["POST"])
def bot_whatsapp():
    incoming_msg = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    # Saludo inicial y menú de opciones con emoji
    if any(word in incoming_msg for word in ["hola", "menu", "empezar", "buenas", "inicio", "pedir"]):
        welcome_text = (
            "¡Hola! Te damos la bienvenida a Pizzería Pedidos y Delivery. 🍕\n\n"
            "¿Qué consulta deseás realizar hoy? Por favor, elegí una opción:\n"
            "1️⃣ Ver Catálogo Completo\n"
            "2️⃣ Consulta por algún Producto por Código (Solapa: Menu y Productos)\n"
            "3️⃣ Consulta por Promos y Combos (Solapa: Promociones y Combos)\n\n"
            "Respondé con el número de la opción que prefieras."
        )
        msg.body(welcome_text)
        
    elif "1" in incoming_msg:
        try:
            # Lee la solapa 'Menu y Productos' del Excel
            df = pd.read_excel(EXCEL_FILE, sheet_name='Menu y Productos')
            
            catalogo_texto = "📄 *Catálogo Completo de Productos:*\n\n"
            # Recorre las filas del Excel para armar la lista (ajusta los nombres de las columnas según tu planilla)
            for index, row in df.iterrows():
                # Suponiendo que tus columnas se llaman 'Codigo', 'Producto' y 'Precio'
                codigo = row.get('Codigo', index)
                nombre = row.get('Producto', 'Sin nombre')
                precio = row.get('Precio', '')
                catalogo_texto += f"▪️ [{codigo}] {nombre} - ${precio}\n"
                
            msg.body(catalogo_texto)
        except Exception as e:
            msg.body("Hubo un error al leer el catálogo de productos. Por favor, intenta más tarde.")
        
    elif "2" in incoming_msg:
        msg.body("Por favor, ingresa el código del producto que deseas consultar (ej: P01).")
        
    elif "3" in incoming_msg:
        msg.body("Aquí tienes nuestras Promos y Combos vigentes. 🎉")
        
    else:
        msg.body("No reconocí tu mensaje. Escribí 'hola' para ver el menú principal.")

    return str(resp)

if __name__ == "__main__":
    app.run() 
