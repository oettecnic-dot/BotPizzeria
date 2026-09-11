import pandas as pd

# 1. Datos de la solapa "Menu y Productos" (+50 ítems, sin comas en descripciones)
menu_data = [
    # --- Pizzas ---
    ("P01", "Pizzas", "Muzarella", "Salsa de tomate - muzarella - orégano y aceitunas", 8500),
    ("P02", "Pizzas", "Fugazzeta", "Cebolla - muzarella y orégano", 9200),
    ("P03", "Pizzas", "Napolitana", "Salsa - muzarella - rodajas de tomate - ajo y perejil", 9500),
    ("P04", "Pizzas", "Calabresa", "Salsa - muzarella y longaniza calabresa", 9800),
    ("P05", "Pizzas", "Jamón y Morrones", "Salsa - muzarella - jamón cocido y morrones asados", 9900),
    ("P06", "Pizzas", "Cuatro Quesos", "Muzarella - roquefort - parmesano y provolone", 10500),
    ("P07", "Pizzas", "Provolone", "Salsa - muzarella y abundante provolone rallado", 10200),
    ("P08", "Pizzas", "Palmitos", "Salsa - muzarella - palmitos y salsa golf", 10600),
    ("P09", "Pizzas", "Rucula y Jamón Crudo", "Salsa - muzarella - rúcula fresca y jamón crudo", 11000),
    ("P10", "Pizzas", "Espinaca a la Crema", "Muzarella - espinaca salteada con crema y queso rallado", 9700),
    ("P11", "Pizzas", "Atún", "Salsa - muzarella - atún desmenuzado y cebolla", 10800),
    ("P12", "Pizzas", "Caprese", "Salsa - muzarella - cubos de tomate - albahaca y aceite de oliva", 9600),
    ("P13", "Pizzas", "Panceta y Huevo", "Salsa - muzarella - panceta ahumada y huevo duro picado", 10400),
    ("P14", "Pizzas", "Americana", "Salsa - muzarella - cheddar - panceta y huevo", 10900),
    ("P15", "Pizzas", "Especial de la Casa", "Salsa - muzarella - jamón - morrones - rodajas de tomate y huevo", 10700),
    
    # --- Empanadas ---
    ("E01", "Empanadas", "Carne Suave", "Cortada a cuchillo con papa - cebolla y especias suaves", 1200),
    ("E02", "Empanadas", "Carne Picante", "Cortada a cuchillo con ají picante y salsa criolla", 1200),
    ("E03", "Empanadas", "Jamón y Queso", "Jamón cocido de primera calidad y muzarella fundida", 1200),
    ("E04", "Empanadas", "Pollo al Verdeo", "Pollo desmenuzado con crema y cebolla de verdeo", 1200),
    ("E05", "Empanadas", "Verde y Salsa Blanca", "Espinaca fresca con salsa blanca y queso parmesano", 1200),
    ("E06", "Empanadas", "Cebolla y Queso (Fugazzeta)", "Cebolla caramelizada con doble muzarella", 1200),
    ("E07", "Empanadas", "Roquefort y Apio", "Queso azul con finos trozos de apio fresco y nuez", 1300),
    ("E08", "Empanadas", "Panceta y Plumitas", "Panceta ahumada con ciruelas y muzarella", 1300),
    ("E09", "Empanadas", "Caprese", "Muzarella - tomate natural fresco y hojas de albahaca", 1200),
    ("E10", "Empanadas", "Humita", "Choclo cremoso con salsa blanca y suave toque de albahaca", 1200),
    ("E11", "Empanadas", "Atún y Verdura", "Atún con cebolla - morrón y un toque de salsa de tomate", 1300),
    ("E12", "Empanadas", "Calabaza y Queso", "Puré de calabaza asada con queso muzarella", 1200),
    ("E13", "Empanadas", "Queso y Provolone", "Mezcla de quesos con provolone estacionado", 1200),
    ("E14", "Empanadas", "Bondiola Braseada", "Bondiola desmenuzada con barbacoa y cebolla caramelizada", 1400),
    ("E15", "Empanadas", "Mexicana", "Carne picada con porotos negros - jalapeño y cheddar", 1400),

    # --- Calzones y Pizzetas ---
    ("C01", "Calzones", "Calzone Clásico", "Relleno de jamón - muzarella - rodajas de tomate y huevo duro", 10500),
    ("C02", "Calzones", "Calzone Fugazzeta", "Relleno de abundante cebolla y triple capa de muzarella", 11000),
    ("C03", "Calzones", "Calzone Completo", "Jamón - morrones - roquefort - muzarella y salsa de tomate", 12000),
    ("C04", "Calzones", "Calzone de Verdura", "Espinaca - acelga - salsa blanca - muzarella y queso rallado", 10800),
    ("C05", "Calzones", "Calzone Pepperoni", "Pepperoni importado - muzarella y salsa de tomate especiada", 11500),
    ("CZ01", "Pizzetas", "Pizzeta Individual Muzarella", "Base de pre-pizza con salsa de tomate y muzarella", 5500),
    ("CZ02", "Pizzetas", "Pizzeta Individual Napolitana", "Salsa - muzarella - tomate en rodajas y ají molido", 5900),
    ("CZ03", "Pizzetas", "Pizzeta Individual Fugazzeta", "Cebolla confitada y muzarella fundida", 5800),
    ("CZ04", "Pizzetas", "Pizzeta Individual Calabresa", "Salsa - muzarella y rodajas de longaniza", 6100),
    ("CZ05", "Pizzetas", "Pizzeta Individual Jamón y Morrones", "Salsa - muzarella - jamón y tiras de morrón", 6300),

    # --- Bebidas y Postres ---
    ("B01", "Bebidas", "Coca Cola 1.5L", "Gaseosa sabor original retornable", 3500),
    ("B02", "Bebidas", "Coca Cola Sin Azúcar 1.5L", "Gaseosa zero azúcares retornable", 3500),
    ("B03", "Bebidas", "Sprite 1.5L", "Gaseosa sabor lima-limón retornable", 3500),
    ("B04", "Bebidas", "Fanta 1.5L", "Gaseosa sabor naranja retornable", 3500),
    ("B05", "Bebidas", "Agua Mineral 1.5L", "Agua sin gas mineralizada", 2200),
    ("B06", "Bebidas", "Agua Saborizada Pomelo 1.5L", "Agua saborizada baja en sodio", 2500),
    ("B07", "Bebidas", "Cerveza Patagonia Amber Lager 710cc", "Cerveza rubia tostada de litro", 4800),
    ("B08", "Bebidas", "Cerveza Stella Artois 1L", "Cerveza lager premium retornable", 4500),
    ("PS01", "Postres", "Helado Bombón Suizo", "Helado de crema americana bañado en chocolate con almendras", 3000),
    ("PS02", "Postres", "Flan Casero con Dulce de Leche", "Porción de flan artesanal con dulce de leche colonial", 3500),
    ("PS03", "Postres", "Queso y Dulce (Almíbar)", "Porción de fresco y batata o membrillo", 2800),
    ("PS04", "Postres", "Tiramisú Tradicional", "Postre clásico italiano con café - vainillas y mascarpone", 4000)
]

# 2. Datos de la solapa "Promociones y Combos"
promos_data = [
    ("COMBO1", "Combos", "Combo Familiar 1", "2 Pizzas de Muzarella - 1 Coca Cola 1.5L", 19500),
    ("COMBO2", "Combos", "Combo Amigos", "1 Pizza Napolitana - 6 Empanadas surtidas - 1 Cerveza 1L", 17200),
    ("COMBO3", "Promos", "Promo Docena de Empanadas", "12 Empanadas a elección con bebida de regalo", 13500),
    ("COMBO4", "Promos", "Promo Individual", "1 Pizzeta Muzarella - 1 Agua Saborizada", 7500)
]

# 3. Creación de DataFrames
df_menu = pd.DataFrame(menu_data, columns=["Codigo", "Categoría", "Producto/ Variedad", "Descripción/Ingredientes", "Precio ($)"])
df_promos = pd.DataFrame(promos_data, columns=["Codigo", "Categoría", "Producto/ Variedad", "Descripción/Ingredientes", "Precio ($)"])

# 4. Generación del archivo Excel en la misma carpeta del proyecto
excel_filename = "Menu y Promos Comercio.xlsx"
with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
    df_menu.to_excel(writer, sheet_name='Menu y Productos', index=False)
    df_promos.to_excel(writer, sheet_name='Promociones y Combos', index=False)

print(f"¡Listo! Archivo '{excel_filename}' creado y corregido con éxito.")