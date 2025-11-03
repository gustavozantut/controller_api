import secrets
from passlib.context import CryptContext

# Para hashing de chaves (semelhante a senhas), bcrypt é uma boa escolha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_api_key(length: int) -> str:
    """
    Gera uma chave de API segura e aleatória.
    Utiliza secrets.token_urlsafe para strings seguras para URL e arquivos.
    """
    return secrets.token_urlsafe(length)


def get_api_key_hash(api_key: str) -> str:
    """
    Cria um hash seguro para uma chave de API em texto puro.
    Este hash será armazenado no banco de dados.
    """
    return pwd_context.hash(api_key[:72])


def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    """
    Verifica se uma chave de API em texto puro corresponde a um hash armazenado.
    """
    return pwd_context.verify(plain_api_key, hashed_api_key)
