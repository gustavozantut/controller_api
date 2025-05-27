#!/bin/bash
# entrypoint.sh

# Esperar pelo banco de dados (altamente recomendado em produção)
# db é o nome do serviço PostgreSQL no docker-compose.yml
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h db -p 5432 -U ${POSTGRES_USER:-postgres}; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done
echo "PostgreSQL is up and running!"

# Rodar migrações do Alembic
echo "Running Alembic migrations..."
alembic upgrade head
echo "Alembic migrations finished."

# Executar o comando principal da aplicação (definido em CMD no Dockerfile)
exec "$@"
