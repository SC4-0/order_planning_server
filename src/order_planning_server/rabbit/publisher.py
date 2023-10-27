import pika
import os


class Publisher:
    def __init__(
        self,
        host=os.environ.get("RABBITMQ_HOST", "localhost"),
        port=os.environ.get("RABBITMQ_PORT", 5672),
        exchange=os.environ.get("RABBITMQ_PUBLISH_EXCHANGE", ""),
    ) -> None:
        self.config = {"host": host, "port": port, "exchange": exchange}

    def connect(self):
        params = pika.ConnectionParameters(
            host=self.config["host"], port=self.config["port"]
        )
        return pika.BlockingConnection(params)

    def publishMessage(self, routing_key, message):
        connection = self.connect()
        channel = connection.channel()
        channel.queue_declare(queue=routing_key)
        channel.basic_publish(
            exchange=self.config["exchange"],
            routing_key=routing_key,
            body=repr(message),
        )
        print("[x] Sent message %r for %r" % (repr(message), routing_key))
        connection.close()
