import os
import pika
import json
from dotenv import load_dotenv, find_dotenv

# Charge automatiquement le premier .env
load_dotenv(find_dotenv())

RABBIT_URL = os.getenv("RABBITMQ_URL")

params = pika.URLParameters(RABBIT_URL)

# Fonction de publication : connexion établie à chaque appel
def publish_client(client: dict):
    # Crée une connexion et un canal à la demande
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange="produits", exchange_type="fanout", durable=True)
    channel.basic_publish(
        exchange="produits",
        routing_key="",
        body=json.dumps(client),
        properties=pika.BasicProperties(content_type='application/json')
    )
    connection.close()
