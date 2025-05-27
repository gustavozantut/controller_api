FROM python:3.10-slim-buster
WORKDIR /app

# Instalar o cliente PostgreSQL para pg_isready
# O comando "nc" (netcat) também pode não estar presente em imagens slim, então adicione-o.
RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*
# Copia os requisitos e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia a pasta 'app' do seu contexto de build (que é /controller_api/app)
# para /app/app dentro do container.
COPY ./app /app/app

# Copia a pasta 'alembic' do seu contexto de build (que é /controller_api/alembic)
# para /app/alembic dentro do container.
COPY ./alembic /app/alembic

# Copia o entrypoint.sh e torna-o executável
COPY ./entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]