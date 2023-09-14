import aio_pika
from aio_pika import RobustConnection
from asyncio import get_event_loop()

loop = get_event_loop()

async def get_broker_conn() -> RobustConnection:
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost", loop=loop)
    return connection

async def publish_to_channel(json_body):
    routing_key = "order_allocation"
    channel: aio_pika.abc.AbstractChannel = await connection.channel()
    await channel.default_exchange.publish(
        aio_pika.Message(
            # encode json_body
        ),
        routing_key=routing_key
    )