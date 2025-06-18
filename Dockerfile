FROM python:3.10-slim-buster

RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*
# Copia os requisitos e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /controller_api
WORKDIR /controller_api
RUN rm requirements.txt
# Copia a pasta 'alembic' do seu contexto de build (que é /controller_api/alembic)
# para /app/alembic dentro do container.

# Copia o entrypoint.sh e torna-o executável
COPY ./entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gunicorn", "app.main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]