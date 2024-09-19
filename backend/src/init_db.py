# Criar um arquivo separado init_db.py para criar as tabelas no banco de dados

# init_db.py
from app import app
from models import db

with app.app_context():
    db.create_all()
