import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Configuración del Bot para Pizzería Pedidos y Delivery
@app.route("/bot", methods=["POST"])
def bot_whatsapp():
    incoming_msg = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    # Saludo inicial y menú de opciones con emoji
    if any(word in incoming_msg for word in ["hola", "menu", "empezar", "buenas", "inicio", "pedir"]):
        welcome_text = (
            "¡Hola! Te damos la bienvenida a Pizzería Pedidos y Delivery. 🍕👋\n\n"
            "¿Qué consulta deseás realizar hoy? Por favor, elegí una opción:\n"
            "1️⃣ Ver Catálogo Completo\n"
            "2️⃣ Consulta por algún Producto por Código (Solapa: Menu y Productos)\n"
            "3️⃣ Consulta por Promos y Combos (Solapa: Promociones y Combos)\n\n"
            "Respondé con el número de la opción que prefieras."
        )
        msg.body(welcome_text)
    
    elif incoming_msg == "1":
        # Opción 1: Catálogo Completo vinculado a la planilla
        msg.body(
            "📋 *Catálogo Completo - Pizzería Pedidos y Delivery*\n\n"
            "Podés acceder a nuestro stock actualizado de más de 50 productos en la planilla oficial: "
            "📂 *Menu y Promos Comercio*."
        )
    
    elif incoming_msg == "2":
        # Opción 2: Búsqueda por código en la solapa 1
        msg.body(
            "🔍 *Consulta por Código (Solapa: Menu y Productos)*\n\n"
            "Por favor, escribí el código exacto del producto (por ejemplo: `P01`, `E01`, `B01`) para buscar su precio y descripción."
        )
    
    elif incoming_msg == "3":
        # Opción 3: Promociones y Combos (Solapa 2)
        msg.body(
            "🔥 *Promociones y Combos (Solapa: Promociones y Combos)*\n\n"
            "Consultá todas nuestras ofertas especiales y combos vigentes actualizados en la segunda solapa de nuestra planilla."
        )
    
    else:
        # Respuesta por defecto ante cualquier otra consulta
        msg.body(
            f"Recibimos tu consulta: \"{incoming_msg}\".\n"
            "Estamos procesando tu pedido o búsqueda en la base de datos *Menu y Promos Comercio*. ¡En instantes te respondemos con el detalle!"
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
