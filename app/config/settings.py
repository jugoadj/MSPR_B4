from dotenv import load_dotenv
import os

load_dotenv()  # Charge les variables depuis .env

# Configuration JWT (existante)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Configuration RabbitMQ (corrigée)
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")  # "localhost" par défaut
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))     # 5672 par défaut
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")       # "guest" par défaut
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "admin") # "guest" par défaut
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")         # "/" par défaut