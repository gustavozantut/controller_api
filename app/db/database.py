from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# URL de conexão do PostgreSQL
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Cria o motor de banco de dados
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Configura a sessão do banco de dados
# autocommit=False: não comita transações automaticamente
# autoflush=False: não libera alterações pendentes automaticamente
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para seus modelos SQLAlchemy
Base = declarative_base()


# Dependência para obter a sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db  # Retorna a sessão para ser usada pelo endpoint
    finally:
        db.close()  # Garante que a sessão seja fechada após o uso
