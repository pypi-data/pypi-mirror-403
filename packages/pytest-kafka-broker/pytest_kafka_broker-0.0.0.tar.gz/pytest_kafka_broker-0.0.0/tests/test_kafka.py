import pytest

topic = "topic"
payload = b"hello world"
group_id = "group_id"


def test_sync(kafka_broker):
    """Demonstrate using the kafka_broker fixture in an ordinary test."""
    with kafka_broker.producer() as producer:
        producer.produce(topic, payload)
    with kafka_broker.consumer(
        {"group.id": group_id, "auto.offset.reset": "earliest"}
    ) as consumer:
        consumer.subscribe([topic])
        (message,) = consumer.consume()
        assert message.value() == payload


@pytest.mark.asyncio
async def test_async(kafka_broker):
    """Demonstrate using the kafka_broker fixture in an async test."""
    producer = kafka_broker.aio_producer()
    try:
        await producer.produce(topic, payload)
    finally:
        # FIXME: use async context manager; see https://github.com/confluentinc/confluent-kafka-python/pull/2180
        await producer.close()
    consumer = kafka_broker.aio_consumer(
        {"group.id": group_id, "auto.offset.reset": "earliest"}
    )
    try:
        await consumer.subscribe([topic])
        (message,) = await consumer.consume()
    finally:
        # FIXME: use async context manager; see https://github.com/confluentinc/confluent-kafka-python/pull/2180
        await consumer.close()
    assert message.value() == payload
