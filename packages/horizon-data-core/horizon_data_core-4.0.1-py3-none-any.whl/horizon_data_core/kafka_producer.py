"""Kafka producer for writing bytes to a configured topic."""

import logging
from typing import Any

from confluent_kafka import KafkaError, Message, Producer

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Kafka producer for writing bytes to a configured topic.

    Simple wrapper around confluent_kafka.Producer that's configured
    for a specific topic. Handles delivery callbacks and flushing.
    """

    def __init__(self, bootstrap_servers: str, topic: str, **kafka_config: Any) -> None:  # noqa: ANN401
        """Initialize the Kafka producer.

        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Kafka topic to produce to
            **kafka_config: Additional confluent_kafka Producer configuration
        """
        self.topic = topic
        config = {"bootstrap.servers": bootstrap_servers, **kafka_config}
        self.producer = Producer(config)
        logger.info("Initialized KafkaProducer for topic=%s", topic)

    def _delivery_callback(self, err: KafkaError | None, msg: Message) -> None:
        """Handle delivery reports for produced messages.

        Args:
            err: Kafka error if delivery failed
            msg: Message metadata from confluent_kafka
        """
        if err is not None:
            logger.error("Message delivery failed: %s", err)
        else:
            logger.debug(
                "Message delivered to %s [%s] at offset %s",
                msg.topic(),
                msg.partition(),
                msg.offset(),
            )

    def produce(self, key: bytes, value: bytes) -> None:
        """Produce a message to the configured Kafka topic.

        Args:
            key: Message key for partitioning
            value: Message payload bytes

        Raises:
            KafkaException: If producer fails to queue the message
        """
        try:
            self.producer.produce(
                topic=self.topic,
                key=key,
                value=value,
                on_delivery=self._delivery_callback,
            )
            # Trigger delivery reports
            self.producer.poll(0)
        except Exception:
            logger.exception("Failed to produce message")
            raise

    def flush(self, timeout: float = 10.0) -> int:
        """Wait for all messages to be delivered.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Number of messages still in queue (0 if all delivered)
        """
        return self.producer.flush(timeout)

    def close(self) -> None:
        """Close the producer and wait for all messages to be delivered."""
        logger.info("Closing IcebergKafkaProducer, flushing pending messages...")
        remaining = self.flush(timeout=30.0)
        if remaining > 0:
            logger.warning("%d messages were not delivered before timeout", remaining)
        else:
            logger.info("All messages delivered successfully")
