import os
import urllib.parse
import logging
import time
from functools import wraps
import pandas as pd
import gspread
from flask import Flask, request, render_template_string, jsonify
from twilio.twiml.messaging_response import MessagingResponse

# Configuración profesional de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

app = Flask(__name__)

# ID de Google Sheets obtenido desde las Variables de Entorno de Render
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "1GB6AVyHP4N63i4FrKXw6I1DR087Mm5F0xEGYnF_0_Fk")

# Memoria temporal para los carritos, estados de pago y nombres de cada cliente/sesión
carritos_clientes = {}
pagos_clientes = {}
nombres_clientes = {}
pidiendo_nombre = {}

# --- FUNCIÓN CORREGIDA PARA DESCONTAR STOCK EN GOOGLE SHEETS ---
def actualizar_stock_google_sheets(carrito):
    """Busca cada producto del carrito por su Código y descuenta el stock en la Columna C ('Stock')."""
    try:
        # Autenticación con gspread usando credenciales locales o configuradas
        gc = gspread.service_account(filename="credenciales.json")
        sh = gc.open_by_key(GOOGLE_SHEET_ID)
        
        pestañas = ["Menu y Productos", "Promociones y Combos"]
        
        for item in carrito:
            codigo_item = str(item.get('codigo', '')).strip().upper()
            cantidad_pedida = int(item.get('cantidad', 1))
            
            if not codigo_item:
                continue

            for nombre_pestaña in pestañas:
                try:
                    worksheet = sh.worksheet(nombre_pestaña)
                    
                    # Obtenemos todos los valores de la primera columna (códigos) para buscar la fila exacta
                    columna_codigos = worksheet.col_values(1)
                    
                    fila_encontrada = None
                    for idx, val in enumerate(columna_codigos, start=1):
                        if str(val).strip().upper() == codigo_item:
                            fila_encontrada = idx
                            break
                    
                    if fila_encontrada:
                        # Columna C corresponde al Stock (Columna 3 según tu planilla)
                        col_stock_idx = 3 
                        
                        # Leemos el valor actual de la celda de stock
                        val_actual = worksheet.cell(fila_encontrada, col_stock_idx).value
                        stock_actual = int(val_actual) if val_actual and str(val_actual).isdigit() else 0
                        
                        # Calculamos el nuevo stock evitando números negativos
                        nuevo_stock = max(0, stock_actual - cantidad_pedida)
                        
                        # Actualizamos la celda en Google Sheets
                        worksheet.update_cell(fila_encontrada, col_stock_idx, nuevo_stock)
                        logging.info(f"✅ [STOCK DESCONTADO] Pestaña '{nombre_pestaña}' | Código: {codigo_item} | Stock anterior: {stock_actual} | Nuevo stock: {nuevo_stock}")
                        break
                except Exception as ex_pestaña:
                    logging.warning(f"No se pudo actualizar en la pestaña '{nombre_pestaña}': {ex_pestaña}")
                    continue

        # Limpiamos la caché para que la próxima lectura traiga el stock actualizado
        if hasattr(obtener_datos_excel, 'cache_clear'):
            obtener_datos_excel.cache_clear()

    except Exception as e:
        logging.error(f"⚠️ Error crítico al descontar stock en Google Sheets: {e}")

# --- DECORADOR DE CACHÉ TTL (Expira cada 5 minutos) ---
def ttl_cache(ttl_seconds=300):
    def decorator(func):
        cache = {}
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            key = str(args) + str(kwargs)
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl_seconds:
                    logging.info("⚡ Usando datos en caché de Google Sheets.")
                    return result
            
            logging.info("🔄 Descargando datos frescos desde Google Sheets...")
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result
        return wrapper
    return decorator

# Función auxiliar para leer los datos de Google Sheets con Caché
@ttl_cache(ttl_seconds=300)
def obtener_datos_excel():
    try:
        sheet_menu = urllib.parse.quote("Menu y Productos")
        sheet_promos = urllib.parse.quote("Promociones y Combos")
        
        url_menu = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_menu}"
        url_promos = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_promos}"
        
        df_menu = pd.read_csv(url_menu)
        df_promos = pd.read_csv(url_promos)
        return df_menu, df_promos
    except Exception as e:
        logging.error(f"Error al leer Google Sheets: {e}")
        return None, None

def limpiar_texto(texto):
    if pd.isna(texto):
        return ""
    return str(texto).replace('&', 'y').strip()

# --- LÓGICA CENTRAL DEL BOT ---
def procesar_logica_bot(remitente, incoming_msg, profile_name=None):
    msg_lower = incoming_msg.strip().lower()
    logging.info(f"Mensaje recibido de [{remitente}] ({profile_name}): {incoming_msg}")

    if remitente not in carritos_clientes:
        carritos_clientes[remitente] = []
    if remitente not in pagos_clientes:
        pagos_clientes[remitente] = "ninguno"
    if remitente not in pidiendo_nombre:
        pidiendo_nombre[remitente] = False

    if profile_name and remitente not in nombres_clientes:
        nombres_clientes[remitente] = profile_name

    respuesta_texto = ""

    # 0. PRIORIDAD 1: Selección de método de pago y confirmación final
    if pagos_clientes[remitente] == "pendiente":
        if msg_lower in ["1", "2", "3"]:
            carrito = carritos_clientes.get(remitente, [])
            total_apagar = sum(item['precio'] for item in carrito)
            nombre_cliente = nombres_clientes.get(remitente) or profile_name or "Cliente"
            
            if msg_lower == "1":
                metodo = "Efectivo (contra entrega)"
                instrucciones = "Tené en cuenta el monto exacto si es posible para facilitar el vuelto."
            elif msg_lower == "2":
                metodo = "Transferencia Bancaria"
                instrucciones = "Alias para transferir: *pizzeria.delivery.mp*\n(Envíanos el comprobante)."
            else:
                metodo = "Mercado Pago"
                instrucciones = "Podés abonar con dinero en cuenta al momento de recibir o solicitar link de pago."

            # 🚀 DISPARA EL DESCUENTO AUTOMÁTICO DE STOCK EN GOOGLE SHEETS
            actualizar_stock_google_sheets(carrito)

            respuesta_texto = (
                f"✅ ¡Pedido confirmado con éxito, {nombre_cliente}!\n\n"
                f"🛒 Total a Pagar: ${total_apagar}\n"
                f"💳 Método de pago: {metodo}\n\n"
                f"ℹ️ {instrucciones}\n\n"
                "En breve nos pondremos en contacto para coordinar el envío. ¡Muchas gracias por elegirnos! 🍕"
            )
            carritos_clientes[remitente] = []
            pagos_clientes[remitente] = "finalizado"
            logging.info(f"Pedido finalizado con éxito para {nombre_cliente} ({remitente}).")
        else:
            respuesta_texto = "⚠️ Por favor, respondé con un número válido para el pago:\n1️⃣ Efectivo\n2️⃣ Transferencia\n3️⃣ Mercado Pago"

    # 1. PRIORIDAD 2: Saludo inicial
    elif any(word in msg_lower for word in ["hola", "buenas", "menu", "empezar", "comenzar", "pedir"]):
        pagos_clientes[remitente] = "ninguno"
        pidiendo_nombre[remitente] = True  
        respuesta_texto = (
            "¡Hola! Te damos la bienvenida a Pizzería Pedidos y Delivery. 🍕\n\n"
            "😊 ¿Cómo te llamás? Así ya te registramos para el pedido:"
        )

    # 2. PRIORIDAD 3: Captura de nombre
    elif pidiendo_nombre.get(remitente, False):
        nombres_clientes[remitente] = incoming_msg.strip()
        pidiendo_nombre[remitente] = False  
        respuesta_texto = (
            f"¡Mucho gusto, *{limpiar_texto(incoming_msg)}*! 🍕👍\n\n"
            "¿Qué deseas ver hoy? Elegí una opción:\n"
            "1️⃣ Ver Menú Completo (Pizzas, Empanadas, Sándwiches, Bebidas) 📋\n"
            "2️⃣ Buscar producto por Código 🔍\n"
            "3️⃣ Promos y Combos 🎉\n\n"
            "💡 También podés escribir directamente el código de cualquier producto (ej: P01, E02, S01) para sumarlo."
        )

    # 3. Opción 1: Menú Completo
    elif msg_lower == "1":
        df_menu, _ = obtener_datos_excel()
        if df_menu is not None:
            catalogo_resumen = "📋 *Menú Completo - Pizzería Pedidos y Delivery* 🍕\n\n"
            
            col_categoria = next((c for c in df_menu.columns if 'producto' in c.lower()), None)
            col_variedad = next((c for c in df_menu.columns if 'variedad' in c.lower()), None)
            col_codigo = next((c for c in df_menu.columns if 'codigo' in c.lower()), df_menu.columns[0])
            col_precio = next((c for c in df_menu.columns if 'precio' in c.lower()), df_menu.columns[-1])

            if col_categoria:
                for categoria, grupo in df_menu.groupby(col_categoria):
                    catalogo_resumen += f"*{str(categoria).upper()}*\n"
                    for _, row in grupo.iterrows():
                        codigo = limpiar_texto(row.get(col_codigo, ''))
                        variedad = limpiar_texto(row.get(col_variedad, '')) if col_variedad else ""
                        nombre_item = f"{categoria} {variedad}".strip() if variedad else str(categoria)
                        precio = row.get(col_precio, 0)
                        catalogo_resumen += f"• `{codigo}` - {nombre_item}: ${precio}\n"
                    catalogo_resumen += "\n"
            else:
                for _, row in df_menu.iterrows():
                    codigo = limpiar_texto(row.get(col_codigo, ''))
                    variedad = limpiar_texto(row.get(col_variedad, ''))
                    precio = row.get(col_precio, 0)
                    catalogo_resumen += f"• `{codigo}` - {variedad}: ${precio}\n"

            catalogo_resumen += "\n*(Escribí el código del producto para sumarlo a tu pedido o 'total' para ver tu carrito).* "
            respuesta_texto = catalogo_resumen
        else:
            respuesta_texto = "📋 *Menú Completo*\n\nNo se pudo conectar con Google Sheets en este momento."

    # 4. Opción 2: Consultar por código
    elif msg_lower == "2":
        respuesta_texto = (
            "🔍 *Consulta por Producto por Código*\n\n"
            "Por favor, escribí el código exacto del producto (por ejemplo: `P01` para pizzas, `E01` para empanadas) y lo sumaremos a tu carrito."
        )

    # 5. Opción 3: Promos y Combos
    elif msg_lower == "3":
        _, df_promos = obtener_datos_excel()
        if df_promos is not None:
            promos_resumen = "🎉 *Promos y Combos Vigentes* 🍕🍻\n\n"
            col_cod = next((c for c in df_promos.columns if 'codigo' in c.lower()), df_promos.columns[0])
            col_prod = next((c for c in df_promos.columns if 'producto' in c.lower() or 'nombre' in c.lower()), df_promos.columns[1])
            col_prec = next((c for c in df_promos.columns if 'precio' in c.lower()), df_promos.columns[-1])

            for _, row in df_promos.iterrows():
                codigo = limpiar_texto(row.get(col_cod, ''))
                nombre = limpiar_texto(row.get(col_prod, ''))
                precio = row.get(col_prec, 0)
                promos_resumen += f"• *{codigo}* - *{nombre}*\n  Precio: *${precio}*\n\n"
            promos_resumen += "*(Escribí el código de la promo para sumarla a tu pedido).* "
            respuesta_texto = promos_resumen
        else:
            respuesta_texto = "🎉 *Promos y Combos*\n\nNo se pudieron cargar las promociones."

    # 6. Ver total / carrito
    elif msg_lower in ["total", "carrito", "pedido"]:
        carrito = carritos_clientes[remitente]
        if not carrito:
            respuesta_texto = "🛒 *Tu carrito está vacío.*\n\nEscribí un código de producto (ej: `P01`) para empezar a sumar."
        else:
            detalle = "🛒 *Resumen de tu Pedido:*\n\n"
            total_apagar = 0
            for item in carrito:
                detalle += f"• {item['nombre']} — ${item['precio']}\n"
                total_apagar += item['precio']
            detalle += f"\n💰 *Total a Pagar: ${total_apagar}*\n\n¿Deseás confirmar tu pedido? Escribí *'confirmar'*."
            respuesta_texto = detalle

    # 7. Vaciar carrito
    elif msg_lower in ["vaciar", "limpiar"]:
        carritos_clientes[remitente] = []
        pagos_clientes[remitente] = "ninguno"
        respuesta_texto = "🗑️ Has vaciado tu carrito. Podés volver a armar tu pedido cuando quieras."

    # 8. Confirmar pedido
    elif msg_lower in ["confirmar", "finalizar"]:
        carrito = carritos_clientes[remitente]
        if not carrito:
            respuesta_texto = "Tu carrito está vacío, no hay nada que confirmar."
        else:
            pagos_clientes[remitente] = "pendiente"
            respuesta_texto = (
                "💳 *Seleccioná tu forma de pago:*\n\n"
                "1️⃣ Efectivo (Pago contra entrega)\n"
                "2️⃣ Transferencia Bancaria\n"
                "3️⃣ Mercado Pago\n\n"
                "Respondé con el número de la opción elegida (1, 2 o 3)."
            )

    else:
        # Búsqueda global por código de producto o combo
        df_menu, df_promos = obtener_datos_excel()
        producto_encontrado = None
        
        if df_menu is not None:
            col_cod = next((c for c in df_menu.columns if 'codigo' in c.lower()), df_menu.columns[0])
            match = df_menu[df_menu[col_cod].astype(str).str.strip().str.lower() == incoming_msg.lower()]
            if not match.empty:
                row = match.iloc[0]
                col_prod = next((c for c in df_menu.columns if 'producto' in c.lower()), '')
                col_var = next((c for c in df_menu.columns if 'variedad' in c.lower()), '')
                col_prec = next((c for c in df_menu.columns if 'precio' in c.lower()), df_menu.columns[-1])
                
                prod_str = limpiar_texto(row.get(col_prod, ''))
                var_str = limpiar_texto(row.get(col_var, ''))
                nombre_comp = f"{prod_str} {var_str}".strip() if var_str else prod_str
                
                producto_encontrado = {
                    'codigo': incoming_msg.strip().upper(),
                    'nombre': nombre_comp,
                    'precio': float(row.get(col_prec, 0)),
                    'cantidad': 1
                }

        if not producto_encontrado and df_promos is not None:
            col_cod = next((c for c in df_promos.columns if 'codigo' in c.lower()), df_promos.columns[0])
            match = df_promos[df_promos[col_cod].astype(str).str.strip().str.lower() == incoming_msg.lower()]
            if not match.empty:
                row = match.iloc[0]
                col_prod = next((c for c in df_promos.columns if 'producto' in c.lower() or 'nombre' in c.lower()), df_promos.columns[1])
                col_prec = next((c for c in df_promos.columns if 'precio' in c.lower()), df_promos.columns[-1])
                
                nombre_comp = limpiar_texto(row.get(col_prod, ''))
                
                producto_encontrado = {
                    'codigo': incoming_msg.strip().upper(),
                    'nombre': nombre_comp,
                    'precio': float(row.get(col_prec, 0)),
                    'cantidad': 1
                }

        if producto_encontrado:
            carritos_clientes[remitente].append(producto_encontrado)
            total_parcial = sum(item['precio'] for item in carritos_clientes[remitente])
            respuesta_texto = (
                f"✅ ¡Agregado a tu pedido!\n"
                f"• *{producto_encontrado['nombre']}* (${producto_encontrado['precio']})\n\n"
                f"🛒 Subtotal parcial: *${total_parcial}*\n"
                f"*(Escribí 'total' para ver tu carrito o seguí agregando más productos).* "
            )
            logging.info(f"Producto agregado al carrito de {remitente}: {producto_encontrado['nombre']}")
        else:
            respuesta_texto = (
                f"Recibimos tu mensaje: \"{incoming_msg}\".\n"
                "Para ver las opciones principales, escribí **'Hola'**, o enviá el código de un producto para sumarlo a tu pedido."
            )

    return respuesta_texto

# --- RUTA WEB INTERACTIVA (Chat en la URL) ---
@app.route("/", methods=["GET"])
def home():
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chat Bot - Pizzería 🍕</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #e5ddd5; margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .chat-container { width: 100%; max-width: 450px; height: 90vh; background: #ffffff; display: flex; flex-direction: column; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); overflow: hidden; }
            .chat-header { background: #075e54; color: white; padding: 15px; text-align: center; font-size: 18px; font-weight: bold; }
            .chat-messages { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #efeae2; }
            .message { max-width: 75%; padding: 10px 14px; border-radius: 8px; font-size: 14px; line-height: 1.4; white-space: pre-wrap; }
            .message.user { background: #dcf8c6; align-self: flex-end; border-bottom-right-radius: 0; }
            .message.bot { background: #ffffff; align-self: flex-start; border-bottom-left-radius: 0; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
            .chat-input-area { display: flex; padding: 10px; background: #f0f0f0; border-top: 1px solid #ddd; }
            .chat-input-area input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 20px; outline: none; font-size: 14px; }
            .chat-input-area button { background: #128c7e; color: white; border: none; padding: 10px 20px; margin-left: 8px; border-radius: 20px; cursor: pointer; font-weight: bold; }
            .chat-input-area button:hover { background: #075e54; }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">🍕 Pizzería Bot - Chat Web</div>
            <div class="chat-messages" id="chatMessages">
                <div class="message bot">¡Hola! Escribí **"Hola"** para comenzar tu pedido en línea. 👋</div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="userInput" placeholder="Escribí un mensaje..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Enviar</button>
            </div>
        </div>

        <script>
            let sessionId = localStorage.getItem("web_session_id");
            if (!sessionId) {
                sessionId = "web_" + Math.random().toString(36).substring(2, 9);
                localStorage.setItem("web_session_id", sessionId);
            }

            function handleKeyPress(event) {
                if (event.key === "Enter") {
                    sendMessage();
                }
            }

            async function sendMessage() {
                const input = document.getElementById("userInput");
                const text = input.value.trim();
                if (!text) return;

                appendMessage(text, "user");
                input.value = "";

                try {
                    const response = await fetch("/chat-api", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ message: text, session_id: sessionId })
                    });
                    const data = await response.json();
                    appendMessage(data.reply, "bot");
                } catch (error) {
                    appendMessage("⚠️ Error de conexión con el servidor.", "bot");
                }
            }

            function appendMessage(text, sender) {
                const messagesContainer = document.getElementById("chatMessages");
                const msgDiv = document.createElement("div");
                msgDiv.className = `message ${sender}`;
                msgDiv.innerText = text;
                messagesContainer.appendChild(msgDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

# --- API PARA CHAT WEB ---
@app.route("/chat-api", methods=["POST"])
def chat_api():
    data = request.get_json()
    incoming_msg = data.get("message", "")
    session_id = data.get("session_id", "web_default")
    
    respuesta = procesar_logica_bot(session_id, incoming_msg)
    return jsonify({"reply": respuesta})

# --- WEBHOOK DE WHATSAPP ---
@app.route("/bot", methods=["POST"])
def bot_whatsapp():
    remitente = request.values.get('From', '')
    incoming_msg = request.values.get('Body', '').strip()
    profile_name = request.values.get('ProfileName', 'Cliente')
    
    resp = MessagingResponse()
    respuesta = procesar_logica_bot(remitente, incoming_msg, profile_name)
    
    resp.message(respuesta)
    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False) 
