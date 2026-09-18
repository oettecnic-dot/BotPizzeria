import os
import pandas as pd

def obtener_menu_desde_sheets():
    """
    Lee el menú de la pizzería desde Google Sheets usando Pandas.
    """
    try:
        sheet_url = os.environ.get('SHEET_URL', 'TU_ENLACE_DE_GOOGLE_SHEETS_CSV')
        df = pd.read_csv(sheet_url)
        menu = df.to_dict(orient='records')
        return menu
    except Exception as e:
        print(f"Error al leer Google Sheets: {e}")
        return [
            {"id": 1, "nombre": "Muzarella", "precio": 8000},
            {"id": 2, "nombre": "Especial", "precio": 9500},
            {"id": 3, "nombre": "Fugazzeta", "precio": 9000}
        ]
