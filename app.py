import os
import json
import requests
import gspread
import pandas as pd
from flask import Flask, request, jsonify

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

# Resto de tu lógica y rutas del bot continúan aquí... 
