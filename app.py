import os
import pandas as pd
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Memoria temporal para los carritos, estados de pago y nombres de cada cliente
carritos_clientes = {}
pagos_clientes = {}
nombres_clientes = {}
pidiendo_nombre = {}

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

    # Inicializamos las estructuras del cliente si es la primera vez que escribe
    if remitente not in carritos_clientes:
        carritos_clientes[remitente] = []
    if remitente not in pagos_clientes:
        pagos_clientes[remitente] = "ninguno"
    if remitente not in pidiendo_nombre:
        pidiendo_nombre[remitente] = False

    # 0. PRIORIDAD 1: Si el cliente está en medio de elegir un método de pago
    if pagos_clientes[remitente] == "pendiente":
        if msg_lower in ["1", "2", "3"]:
            carrito = carritos_clientes.get(remitente, [])
            total_apagar = sum(item['precio'] for item in carrito)
            nombre_cliente = nombres_clientes.get(remitente, "Cliente")
            
            if msg_lower == "1":
                metodo = "Efectivo (contra entrega)"
                instrucciones = "Tené en cuenta el monto exacto si es posible para facilitar el vuelto."
            elif msg_lower == "2":
                metodo = "Transferencia Bancaria"
                instrucciones = "Alias para transferir: *pizzeria.delivery.mp*\n(Envíanos el comprobante por este medio)."
            else:
                metodo = "Mercado Pago"
                instrucciones = "Podés abonar con dinero en cuenta al momento de recibir o solicitar link de pago."

            msg.body(
                f"✅ ¡Pedido confirmado con éxito, {nombre_cliente}!\n\n"
                f"🛒 *Total a Pagar:* ${total_apagar}\n"
                f"💳 *Método de pago:* {metodo}\n\n"
                f"ℹ️ {instrucciones}\n\n"
                "En breve nos pondremos en contacto para coordinar el envío. ¡Muchas gracias por elegirnos! 🍕"
            )
            
            carritos_clientes[remitente] = []
            pagos_clientes[remitente] = "finalizado"
        else:
            msg.body("⚠️ Por favor, respondé con un número válido para el pago:\n1️⃣ Efectivo\n2️⃣ Transferencia\n3️⃣ Mercado Pago")

    # 1. PRIORIDAD 2: Activación con el saludo "hola" o similar
    elif any(word in msg_lower for word in ["hola", "buenas", "menu", "empezar", "comenzar", "pedir"]):
        pagos_clientes[remitente] = "ninguno"
        pidiendo_nombre[remitente] = True  # Activamos la bandera para capturar el nombre en el siguiente mensaje
        welcome_text = (
            "¡Hola! Te damos la bienvenida a Pizzería Pedidos y Delivery. 🍕\n\n"
            "😊 ¿Cómo te llamás? Así ya te registramos para el pedido:"
        )
        msg.body(welcome_text)

    # 2. PRIORIDAD 3: Si el bot estaba esperando el nombre del cliente
    elif pidiendo_nombre.get(remitente, False):
        nombres_clientes[remitente] = incoming_msg
        pidiendo_nombre[remitente] = False  # Desactivamos la bandera
        
        # Le saludamos por su nombre y le mostramos el menú principal de inmediato
        menu_opciones = (
            f"¡Mucho gusto, *{incoming_msg}*! 🍕👍\n\n"
            "¿Qué deseas ver hoy? Elegí una opción:\n"
            "1️⃣ Pizzas 🍕\n"
            "2️⃣ Empanadas 🥟\n"
            "3️⃣ Promos y Combos 🎉\n\n"
            "💡 También podés escribir directamente el código de un producto o combo (ej: P14 o COMBO01) para ver sus detalles."
        )
        msg.body(menu_opciones)

    # 3. Opción 1: Filtrar y mostrar solo Pizzas 🍕
    elif msg_lower == "1":
        df_menu, _ = obtener_datos_excel()
        if df_menu is not None:
            pizzas = df_menu[df_menu.astype(str).str.contains('pizza', case=False).any(axis=1)]
            if pizzas.empty:
                pizzas = df_menu
                
            catalogo_resumen = "🍕 *Catálogo de Pizzas* 🍕\n\n"
            for _, row in pizzas.iterrows():
                codigo = row.get('Codigo', row.iloc[0])
                nombre = row.get('Producto/ Variedad', row.iloc[1])
                precio = row.get('Precio ($)', row.iloc[-1])
                catalogo_resumen += f"• `{codigo}` - {nombre}: ${precio}\n"
                
            catalogo_resumen += "\n*(Escribí el código del producto para sumarlo a tu pedido o 'total' para ver tu carrito).* "
            msg.body(catalogo_resumen)
        else:
            msg.body("🍕 *Pizzas*\n\nEstamos actualizando el catálogo de pizzas.")

    # 4. Opción 2: Filtrar y mostrar solo Empanadas 🥟
    elif msg_lower == "2":
        df_menu, _ = obtener_datos_excel()
        if df_menu is not None:
            empanadas = df_menu[df_menu.astype(str).str.contains('empanada', case=False).any(axis=1)]
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
            msg.body("🥟 *Empanadas*\n\nEstamos actualizando el catálogo de empanadas.")

    # 5. Opción 3: Consultar promos o combos 🎉
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
            msg.body("🎉 *Promos y Combos*\n\nConsultá nuestras ofertas especiales actualizadas.")

    # 6. Ver el total y el carrito actual
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

    # 7. Vaciar el carrito
    elif msg_lower in ["vaciar", "limpiar"]:
        carritos_clientes[remitente] = []
        pagos_clientes[remitente] = "ninguno"
        msg.body("🗑️ Has vaciado tu carrito. Podés volver a armar tu pedido cuando quieras.")

    # 8. Iniciar confirmación de pedido (Pide elegir forma de pago)
    elif msg_lower in ["confirmar", "finalizar"]:
        carrito = carritos_clientes[remitente]
        if not carrito:
            msg.body("Tu carrito está vacío, no hay nada que confirmar.")
        else:
            pagos_clientes[remitente] = "pendiente"
            msg.body(
                "💳 *Seleccioná tu forma de pago:*\n\n"
                "1️⃣ Efectivo (Pago contra entrega)\n"
                "2️⃣ Transferencia Bancaria\n"
                "3️⃣ Mercado Pago\n\n"
                "Respondé con el número de la opción elegida (1, 2 o 3)."
            )

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
