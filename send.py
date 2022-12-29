import pika
import json
import logging

from settings import Settings


settings: Settings = Settings()
logging.basicConfig(level=logging.INFO)


def rabbit_queue(message: dict) -> None:
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=settings.Rabbit_host)
    )
    channel = connection.channel()
    channel.queue_declare(queue=str(settings.Rabbit_chanel))

    channel.basic_publish(
        exchange="", routing_key=str(settings.Rabbit_chanel), body=json.dumps(message)
    )
    logging.info("Send message: %s", json.dumps(message))
    connection.close()
