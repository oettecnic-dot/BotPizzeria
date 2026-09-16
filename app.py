import os
import pandas as pd
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Memoria temporal para los carritos de cada cliente (clave: número de teléfono, valor: lista de productos)
carritos_clientes = {}

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
    # Obtenemos el teléfono del cliente y el mensaje que envió
    remitente = request.values.get('From', '')
    incoming_msg = request.values.get('Body', '').strip()
    msg_lower = incoming_msg.lower()
    
    resp = MessagingResponse()
    msg = resp.message()

    # Inicializamos el carrito del cliente si es la primera vez que escribe
    if remitente not in carritos_clientes:
        carritos_clientes[remitente] = []

    # 1. Activación con el saludo "hola" o similar
    if any(word in msg_lower for word in ["hola", "buenas", "menu", "empezar", "comenzar", "pedir"]):
        welcome_text = (
            "¡Hola! Te damos la bienvenida a Pizzería Pedidos y Delivery. 🍕\n\n"
            "¿Qué deseas ver hoy? Elegí una opción:\n"
            "1️⃣ Pizzas 🍕\n"
            "2️⃣ Empanadas 🥟\n"
            "3️⃣ Promos y Combos 🎉\n\n"
            "💡 También podés escribir directamente el código de un producto o combo (ej: P14 o COMBO01) para ver sus detalles."
        )
        msg.body(welcome_text)
    
    # 2. Opción 1: Filtrar y mostrar solo Pizzas 🍕
    elif msg_lower == "1":
        df_menu, _ = obtener_datos_excel()
        if df_menu is not None:
            # Buscamos filas que pertenezcan a la categoría de Pizzas (ajustá la palabra clave si tu Excel usa otra denominación)
            pizzas = df_menu[df_menu.astype(str).apply(lambda row: row.str.contains('pizza', case=False).any(), axis=1)]
            
            if pizzas.empty:
                pizzas = df_menu # Si no encuentra categoría específica, muestra todo el menú general
                
            catalogo_resumen = "🍕 *Catálogo de Pizzas* 🍕\n\n"
            for _, row in pizzas.iterrows():
                # Tratamos de ubicar las columnas comunes de código, producto y precio
                codigo = row.get('Codigo', row.iloc[0])
                nombre = row.get('Producto/ Variedad', row.iloc[1])
                precio = row.get('Precio ($)', row.iloc[-1])
                catalogo_resumen += f"• `{codigo}` - {nombre}: ${precio}\n"
                
            catalogo_resumen += "\n*(Escribí el código del producto para sumarlo a tu pedido o 'total' para ver tu carrito).* "
            msg.body(catalogo_resumen)
        else:
            msg.body("🍕 *Pizzas*\n\nEstamos actualizando el catálogo de pizzas. ¡En instantes te enviamos el detalle!")

    # 3. Opción 2: Filtrar y mostrar solo Empanadas 🥟
    elif msg_lower == "2":
        df_menu, _ = obtener_datos_excel()
        if df_menu is not None:
            empanadas = df_menu[df_menu.astype(str).apply(lambda row: row.str.contains('empanada', case=False).any(), axis=1)]
            
            if empanadas.empty:
                empanadas = df_menu
                
            catalogo_resumen = "🥟 *Catálogo de Empanadas* 🥟\n\n"
            for _, row in empanadas.iterrows():
                codigo = row.get('Codigo', row.iloc[0])
                nombre = row.get('Producto/ Variedad', row.iloc[1])
                precio = row.get('Precio ($)', row.iloc[-1])
                catalogo_resumen += f"• `{codigo}` - {nombre}: ${precio}\n"
                
            catalogo_resumen += "\n*(Escribí el código del producto para sumarlo a tu pedido o 'total' para ver tu carrito).* "
            msg.body(catalogo_resumen)
        else:
            msg.body("🥟 *Empanadas*\n\nEstamos actualizando el catálogo de empanadas. ¡En instantes te enviamos el detalle!")

    # 4. Opción 3: Consultar promos o combos 🎉
    elif msg_lower == "3":
        _, df_promos = obtener_datos_excel()
        if df_promos is not None:
            promos_resumen = "🎉 *Promos y Combos Vigentes* 🍕🍻\n\n"
            for _, row in df_promos.iterrows():
                codigo = row.get('Codigo', row.iloc[0])
                nombre = row.get('Producto/ Variedad', row.iloc[1])
                desc = row.get('Descripción/Ingredientes', '')
                precio = row.get('Precio ($)', row.iloc[-1])
                
                promos_resumen += f"• *{codigo}* - *{nombre}*\n  _{desc}_\n  Precio: *${precio}*\n\n"
            promos_resumen += "*(Escribí el código del combo para sumarlo a tu pedido).* "
            msg.body(promos_resumen)
        else:
            promos_resumen = "🎉 *Promos y Combos*\n\nConsultá nuestras ofertas especiales actualizadas."
            msg.body(promos_resumen)

    # 5. Ver el total y el carrito actual
    elif msg_lower in ["total", "carrito", "pedido"]:
        carrito = carritos_clientes[remitente]
        if not carrito:
            msg.body("🛒 *Tu carrito está vacío.*\n\nEscribí un código de producto o combo (ej: `P01`) para empezar a sumar a tu pedido.")
        else:
            detalle = "🛒 *Resumen de tu Pedido:*\n\n"
            total_apagar = 0
            for item in carrito:
                detalle += f"• {item['nombre']} — ${item['precio']}\n"
                total_apagar += item['precio']
            
            detalle += f"\n💰 *Total a Pagar: ${total_apagar}*\n\n¿Deseás confirmar tu pedido? Escribí *'confirmar'*."
            msg.body(detalle)

    # 6. Vaciar el carrito
    elif msg_lower in ["vaciar", "limpiar"]:
        carritos_clientes[remitente] = []
        msg.body("🗑️ Has vaciado tu carrito. Podés volver a armar tu pedido cuando quieras escribiendo los códigos de los productos.")

    # 7. Confirmar pedido
    elif msg_lower in ["confirmar", "finalizar"]:
        carrito = carritos_clientes[remitente]
        if not carrito:
            msg.body("Tu carrito está vacío, no hay nada que confirmar.")
        else:
            total_apagar = sum(item['precio'] for item in carrito)
            msg.body(f"✅ ¡Pedido confirmado con éxito!\n\nEl total de tu compra es de *${total_apagar}*.\nEn breve nos pondremos en contacto para coordinar la entrega y el pago. ¡Muchas gracias por elegirnos! 🍕")
            carritos_clientes[remitente] = []

    else:
        # Intentamos buscar si lo que escribió el cliente es un código de producto (ej: P01, E01, COMBO01)
        df_menu, df_promos = obtener_datos_excel()
        producto_encontrado = None
        
        # Buscamos en el menú general
        if df_menu is not None:
            match = df_menu[df_menu['Codigo'].astype(str).str.lower() == incoming_msg.lower()]
            if not match.empty:
                producto_encontrado = {
                    'nombre': match.iloc[0]['Producto/ Variedad'],
                    'precio': float(match.iloc[0]['Precio ($)'])
                }
        
        # Si no está en el menú, buscamos en promos y combos
        if not producto_encontrado and df_promos is not None:
            match = df_promos[df_promos['Codigo'].astype(str).str.lower() == incoming_msg.lower()]
            if not match.empty:
                producto_encontrado = {
                    'nombre': match.iloc[0]['Producto/ Variedad'],
                    'precio': float(match.iloc[0]['Precio ($)'])
                }

        # Si encontramos el producto por código, lo sumamos al carrito
        if producto_encontrado:
            carritos_clientes[remitente].append(producto_encontrado)
            total_parcial = sum(item['precio'] for item in carritos_clientes[remitente])
            msg.body(
                f"✅ ¡Agregado a tu pedido!\n"
                f"• *{producto_encontrado['nombre']}* (${producto_encontrado['precio']})\n\n"
                f"🛒 Subtotal parcial: *${total_parcial}*\n"
                f"*(Escribí 'total' para ver tu carrito o seguí agregando más productos).* "
            )
        else:
            # Si no es un código válido ni un comando conocido
            msg.body(
                f"Recibimos tu mensaje: \"{incoming_msg}\".\n"
                "Para ver las opciones principales, escribí **'Hola'**, o enviá el código de un producto (ej: `P01`) para sumarlo a tu pedido."
            )

    # Devuelve la respuesta obligatoria a Twilio
    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False) 
