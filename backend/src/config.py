# config.py
import os
from datetime import timedelta


class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:pass@localhost/makequestions'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # Ajuste conforme necessário
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # Ajuste conforme necessário
