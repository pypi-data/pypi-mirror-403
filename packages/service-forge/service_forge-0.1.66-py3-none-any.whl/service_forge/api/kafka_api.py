from __future__ import annotations

import asyncio
import inspect
import json
from typing import Any, Callable

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer, ConsumerRecord
from loguru import logger
from opentelemetry import context as otel_context_api
from opentelemetry import trace
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import SpanKind

from service_forge.trace.execution_context import (
    ExecutionContext,
    set_current_context,
    get_current_context,
    reset_current_context,
)


class KafkaApp:
    def __init__(self, bootstrap_servers: str = None):
        self.bootstrap_servers = bootstrap_servers
        self._handlers: dict[str, Callable] = {}
        self._consumer_tasks: dict[str, asyncio.Task] = {}
        self._producer: AIOKafkaProducer = None
        self._lock = asyncio.Lock()
        self._running = False
        self._tracer = trace.get_tracer("service_forge.api.kafka")

    def kafka_input(self, topic: str, data_type: type, group_id: str):
        def decorator(func: Callable):
            self._handlers[topic] = (func, data_type, group_id)
            logger.info(
                f"Registered Kafka input handler for topic '{topic}', data_type: {data_type}"
            )

            if self._running:
                asyncio.create_task(
                    self._start_consumer(topic, func, data_type, group_id)
                )
            return func

        return decorator

    def set_bootstrap_servers(self, bootstrap_servers: str) -> None:
        self.bootstrap_servers = bootstrap_servers

    async def start(self):
        if not self.bootstrap_servers:
            raise ValueError("bootstrap_servers 未设置")

        logger.info(f"🚀 KafkaApp started with servers: {self.bootstrap_servers}")

        await self._start_producer()

        async with self._lock:
            for topic, (handler, data_type, group_id) in self._handlers.items():
                if topic not in self._consumer_tasks:
                    self._consumer_tasks[topic] = asyncio.create_task(
                        self._start_consumer(topic, handler, data_type, group_id)
                    )

        self._running = True
        while self._running:
            await asyncio.sleep(1)

    async def _start_consumer(
        self, topic: str, handler: Callable, data_type: type, group_id: str
    ):
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            enable_auto_commit=True,
            auto_offset_reset="latest",
        )
        await consumer.start()
        logger.info(f"✅ Started consumer for topic: {topic}")

        try:
            async for msg in consumer:
                await self._dispatch_message(handler, msg, data_type)
        except asyncio.CancelledError:
            logger.warning(f"🛑 Consumer for {topic} cancelled")
        finally:
            await consumer.stop()

    async def _dispatch_message(
        self, handler: Callable, msg: ConsumerRecord, data_type: type
    ):
        header_carrier: dict[str, str] = {}
        for key, value in msg.headers or []:
            try:
                header_carrier[key] = (
                    value.decode("utf-8")
                    if isinstance(value, (bytes, bytearray))
                    else str(value)
                )
            except Exception:
                header_carrier[key] = ""

        try:
            parent_context = extract(header_carrier)
        except Exception:
            parent_context = otel_context_api.get_current()
        if parent_context is None:
            parent_context = otel_context_api.get_current()

        span_name = f"Kafka consume {msg.topic}"
        with self._tracer.start_as_current_span(
            span_name,
            context=parent_context,
            kind=SpanKind.CONSUMER,
        ) as span:
            span.set_attribute("messaging.system", "kafka")
            span.set_attribute("messaging.destination", msg.topic)
            span.set_attribute("messaging.kafka.partition", msg.partition)
            span.set_attribute("messaging.kafka.offset", msg.offset)

            execution_context = ExecutionContext(
                trace_context=otel_context_api.get_current(),
                span=span,
                logger=logger.bind(topic=msg.topic),
                metadata={
                    "entrypoint": "kafka",
                    "topic": msg.topic,
                    "partition": msg.partition,
                },
            )
            token = set_current_context(execution_context)

            try:
                try:
                    data = data_type()
                    data.ParseFromString(msg.value)
                except Exception as e:
                    print("Error:", e)
                    data = data_type(**json.loads(msg.value.decode("utf-8")))
                result = handler(data)
                if inspect.iscoroutine(result):
                    await result
            finally:
                reset_current_context(token)

    async def _start_producer(self):
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: v.SerializeToString(),
            )
            await self._producer.start()
            logger.info("✅ Kafka producer started")

    async def _stop_producer(self):
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
            logger.info("✅ Kafka producer stopped")

    async def send_message(self, topic: str, data_type: type, data: Any) -> None:
        if not self._running:
            raise RuntimeError("KafkaApp is not running. Call start() first.")

        if self._producer is None:
            raise RuntimeError("Kafka producer is not initialized.")

        headers_carrier: dict[str, str] = {}
        execution_context = get_current_context()
        try:
            if execution_context and execution_context.trace_context is not None:
                inject(headers_carrier, context=execution_context.trace_context)
            else:
                inject(headers_carrier)
        except Exception as e:
            logger.warning(f"inject trace context failed: {e}")

        try:
            await self._producer.send_and_wait(
                topic,
                data,
                headers=[
                    (key, str(value).encode("utf-8"))
                    for key, value in headers_carrier.items()
                ],
            )
            logger.info(f"✅ 已发送消息到 topic '{topic}', type: {data_type}")

        except Exception as e:
            logger.error(f"❌ 发送消息到 topic '{topic}' 失败: {e}")
            raise

    async def stop(self):
        logger.info("Stopping KafkaApp ...")
        self._running = False

        for t in list(self._consumer_tasks.values()):
            t.cancel()
        await asyncio.sleep(0.1)
        self._consumer_tasks.clear()

        await self._stop_producer()

        logger.info("✅ KafkaApp stopped")


kafka_app = KafkaApp()


async def start_kafka_server(bootstrap_servers: str):
    kafka_app.set_bootstrap_servers(bootstrap_servers)
    await kafka_app.start()
