import os

class Config:
    # Llave secreta de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'una-llave-secreta-por-defecto')
    
    # Configuración de la base de datos de Supabase
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
