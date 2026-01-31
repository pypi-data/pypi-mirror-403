import asyncio
import os
from typing import List, Tuple, Optional, Callable

import aio_pika
from aiormq import AMQPConnectionError

from ..event import Message, Event
from ..util.singleton import SingletonMeta


class RabbitMQ:
    def __init__(self):
        self.connection = None
        self.channel = None
        self._on_reconnect_callbacks = []

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            host=os.getenv('QUEUE_HOST'),
            port=int(os.getenv('QUEUE_PORT')),
            login=os.getenv('QUEUE_USER'),
            password=os.getenv('QUEUE_PASS'),
            virtualhost=os.getenv("QUEUE_VHOST", "/"),
        )
        print("  RabbitMQ - Connected!")
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=int(os.getenv("QUEUE_PREFETCH", "16")))

        # Registreer de reconnect callback op het kanaal, niet de connectie
        self.channel.reopen_callbacks.add(self._on_channel_reopen)
        print("  RabbitMQ - Channel created & QoS set!")

    async def _on_channel_reopen(self, channel):
        print("  RabbitMQ - Channel restored, re-applying settings...")
        await channel.set_qos(prefetch_count=int(os.getenv("QUEUE_PREFETCH", "16")))
        for callback in self._on_reconnect_callbacks:
            await callback()

    async def setup_topology(
        self,
        exchange_name: str,
        exchange_type: aio_pika.ExchangeType = aio_pika.ExchangeType.TOPIC,
        durable: bool = True,
        bindings: List[Tuple[str, str]] = (),
        dlx_name: Optional[str] = None
    ):
        exchange = await self.channel.declare_exchange(
            exchange_name, exchange_type, durable=durable
        )
        print(f"  RabbitMQ - Exchange declared: {exchange_name}")

        # Create queues and bindings
        for queue_name, routing_key in bindings:
            args = {}
            if dlx_name:
                args["x-dead-letter-exchange"] = dlx_name
                args["x-dead-letter-routing-key"] = f"{queue_name}.dead"

            queue = await self.channel.declare_queue(
                queue_name, durable=True, arguments=args
            )
            await queue.bind(exchange, routing_key=routing_key)
            print(f"  RabbitMQ - Queue bound: {queue_name} ←({routing_key})– {exchange_name}")

        # Create DLX
        if dlx_name:
            await self.channel.declare_exchange(dlx_name, aio_pika.ExchangeType.DIRECT, durable=True)

            # Dead-letter queues
            for queue_name, _ in bindings:
                dlq = await self.channel.declare_queue(f"{queue_name}.dlq", durable=True)
                await dlq.bind(dlx_name, routing_key=f"{queue_name}.dead")
                print(f"  RabbitMQ - DLQ bound: {dlq.name} ← {dlx_name}")

    async def consume(self, exchange_name: str, queue: str, callback: Callable, dlx_name: Optional[str] = None):
        while True:
            try:
                print(f"  RabbitMQ - Consuming from queue: {queue}")

                args = {}
                if dlx_name:
                    args["x-dead-letter-exchange"] = dlx_name
                    args["x-dead-letter-routing-key"] = f"{queue}.dead"

                queue_object = await self.channel.declare_queue(queue, durable=True, arguments=args)

                # Bind to exchange if not already bound
                if exchange_name != "default":
                    exchange = await self.channel.get_exchange(exchange_name)
                    await queue_object.bind(exchange, routing_key=queue)

                async for message in queue_object:
                    async with message.process():
                        event: Event = Event.decode(message.body)
                        print(f"  RabbitMQ ({queue}) - [x] Received event: {event.meta.event_type} (trace: {event.meta.trace_id})")
                        await callback(queue, event)
            except (aio_pika.exceptions.AMQPConnectionError, aio_pika.exceptions.ChannelClosed):
                print(f"  RabbitMQ - Connection lost while consuming {queue}. Retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"  RabbitMQ - Unexpected error in consumer {queue}: {e}")
                await asyncio.sleep(5)

    async def send_message(self, message: Message):
        # Haal de exchange op
        if message.exchange == "default":
            exchange = self.channel.default_exchange
            routing_key = message.routing_key
        else:
            exchange = await self.channel.get_exchange(message.exchange)
            routing_key = message.routing_key

        # Bouw aio_pika.Message met alle metadata
        amqp_message = aio_pika.Message(
            body=message.body(),
            headers=message.merged_headers(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT if message.persistent else aio_pika.DeliveryMode.NOT_PERSISTENT,
        )

        await exchange.publish(amqp_message, routing_key=routing_key)
        print(
            f"  RabbitMQ - [x] Sent event: {message.event.meta.event_type} "
            f"to exchange '{message.exchange}' with routing key '{routing_key}' "
            f"(trace: {message.event.meta.trace_id})"
        )


class QueueContext(metaclass=SingletonMeta):

    def __init__(self):
        self._rabbit_mq = RabbitMQ()
        self._message_callbacks = []

    async def connect(self):
        try:
            await self._rabbit_mq.connect()
        except AMQPConnectionError as e:
            print(f"  RabbitMQ - Connection failed: {e}")
            await asyncio.sleep(5)
            await self.connect()


    async def setup_topology(
        self,
        exchange_name: str,
        exchange_type: aio_pika.ExchangeType = aio_pika.ExchangeType.TOPIC,
        durable: bool = True,
        bindings: List[Tuple[str, str]] = (),
        dlx_name: Optional[str] = None
    ):
        await self._rabbit_mq.setup_topology(
            exchange_name, exchange_type, durable, bindings, dlx_name
        )

    async def start_consuming(self, exchange_name: str, queue: str, dlx_name: Optional[str] = None):
        asyncio.create_task(
            self._rabbit_mq.consume(exchange_name, queue, self._on_new_message, dlx_name=dlx_name)
        )

    async def _on_new_message(self, queue: str, event: Event):
        for callback_object in self._message_callbacks:
            if callback_object.get("queue") == queue:
                await callback_object.get("callback")(event)

    def add_on_message_callback(self, queue: str, callback: Callable):
        self._message_callbacks.append({'queue': queue, 'callback': callback})

    async def send_message(self, message: Message):
        await self._rabbit_mq.send_message(message)