import os
import psycopg2

# 1. Obtenha a DATABASE_URL do ambiente (como a API a veria)
db_url = os.environ.get("DATABASE_URL")

print(f"DEBUG: DATABASE_URL lida do ambiente: {db_url}")

# 2. Tente a conexão
try:
    conn = psycopg2.connect(db_url)
    print("DEBUG: Conexão psycopg2 BEM-SUCEDIDA!")
    conn.close()  # Feche a conexão imediatamente após o teste
    print("DEBUG: Conexão fechada.")
except Exception as e:
    print(f"DEBUG: ERRO DE CONEXÃO psycopg2: {e}")

# 3. Opcional: Se a conexão falhou, tente as variáveis separadamente
#    (útil se houver problema no parsing da URL)
print("\nDEBUG: Tentando conectar com variáveis separadas (se a URL falhou):")
try:
    # Estas variáveis só existirão no ambiente se você as injetar via `environment:`
    # no docker-compose.yml ou se a DATABASE_URL for construída no Python
    user = os.environ.get(
        "POSTGRES_USER", "brplates_user"
    )  # Use o padrão se não encontrar
    password = os.environ.get(
        "POSTGRES_PASSWORD", "brplates_pass"
    )  # Use o padrão se não encontrar
    host = os.environ.get("POSTGRES_HOST", "db")
    port = os.environ.get("POSTGRES_PORT", "5432")
    dbname = os.environ.get("POSTGRES_DB", "brplates_db")

    conn_alt = psycopg2.connect(
        user=user, password=password, host=host, port=port, dbname=dbname
    )
    print("DEBUG: Conexão psycopg2 BEM-SUCEDIDA com variáveis separadas!")
    conn_alt.close()
    print("DEBUG: Conexão separada fechada.")
except Exception as e:
    print(f"DEBUG: ERRO DE CONEXÃO psycopg2 com variáveis separadas: {e}")
