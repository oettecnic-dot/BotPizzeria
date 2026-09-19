import os
import json
import requests
import gspread
import pandas as pd
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# ID de Google Sheets obtenido desde las Variables de Entorno de Render
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "1U6BKHy4H4SVI2X-9R0G3pt3f-ps5-R44uE1wmC7s1HAPU7e4")

# Memoria temporal para los carritos, estados de pago y nombres de cada cliente/sesión
carritos_clientes = {}
pagos_clientes = {}
nombres_clientes = {}
pidiendo_nombre = {}

# --- FUNCIÓN NUEVA PARA DESCONTAR STOCK USANDO GOOGLE APPS SCRIPT ---
def actualizar_stock_google_sheets(carrito):
    url_script = os.environ.get("GOOGLE_SCRIPT_URL")
    if not url_script:
        print("❌ Error: GOOGLE_SCRIPT_URL no está configurada en Render")
        return False
    
    for item in carrito:
        codigo = item.get('codigo')
        cantidad = item.get('cantidad', 1)
        
        payload = {
            "codigo": str(codigo),
            "cantidad": int(cantidad)
        }
        
        try:
            response = requests.post(url_script, json=payload)
            resultado = response.json()
            if resultado.get("status") == "success":
                print(f"✅ Stock actualizado para el código {codigo}. Nuevo stock: {resultado.get('nuevo_stock')}")
            else:
                print(f"⚠️ No se encontró el código {codigo} en la planilla.")
        except Exception as e:
            print(f"❌ Error crítico al conectar con Google Script: {e}")
            return False
    return True

# --- RUTA DE WHATSAPP ---
@app.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    incoming_msg = request.form.get('Body', '').strip()
    sender_id = request.form.get('From', '')
    
    resp = MessagingResponse()
    msg = resp.message()
    
    # Inicializar carrito para el usuario si no existe
    if sender_id not in carritos_clientes:
        carritos_clientes[sender_id] = []
    
    texto = incoming_msg.lower()
    
    if texto == 'hola':
        msg.text("¡Hola! Bienvenido a la pizzería. Escribí el código del producto que deseas agregar (por ejemplo: P01, E01) o escribe CONFIRMAR para finalizar tu pedido.")
    elif texto == 'confirmar':
        carrito = carritos_clientes.get(sender_id, [])
        if not carrito:
            msg.text("Tu carrito está vacío. Agrega productos antes de confirmar.")
        else:
            # Descontar stock usando la nueva función del puente web
            exito = actualizar_stock_google_sheets(carrito)
            if exito:
                msg.text("¡Pedido confirmado con éxito! Ya hemos descontado el stock y estamos preparando tu pedido.")
                carritos_clientes[sender_id] = [] # Limpiar carrito
            else:
                msg.text("Hubo un error al actualizar el stock en la planilla. Inténtalo de nuevo más tarde.")
    else:
        # Lógica para agregar productos de ejemplo por código
        codigo_ingresado = incoming_msg.upper()
        carritos_clientes[sender_id].append({"codigo": codigo_ingresado, "cantidad": 1})
        msg.text(f"Producto {codigo_ingresado} agregado al carrito. Escribe CONFIRMAR para terminar tu pedido o sigue agregando más.")

    return str(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 
