import os
import pika
import json
from dotenv import load_dotenv, find_dotenv
from ..config.settings import RABBITMQ_URL


# # Charge automatiquement le premier .env
# load_dotenv(find_dotenv())


params = pika.URLParameters(RABBITMQ_URL)

# Fonction de publication : connexion établie à chaque appel
def publish_product(product: dict):
    # Crée une connexion et un canal à la demande
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange="produits", exchange_type="fanout", durable=True)
    channel.basic_publish(
        exchange="produits",
        routing_key="",
        body=json.dumps(product, default=str),

        properties=pika.BasicProperties(content_type='application/json')
    )
    connection.close()
