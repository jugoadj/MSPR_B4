from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote

DATABASE_URL = "postgresql://postgres:196810@localhost:5432/msprB4Db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# TEST DE CONNEXION À LA BASE DE DONNÉES
def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("✅ Connexion à la base de données réussie.")
    except Exception as e:
        print("❌ Erreur de connexion :", e)

# Appel au test
test_connection()
