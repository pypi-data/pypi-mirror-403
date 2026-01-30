"""Tests for KafkaProducer."""

from unittest.mock import Mock, patch

import pytest

from horizon_data_core.kafka_producer import KafkaProducer


@pytest.fixture
def mock_confluent_producer():
    """Mock confluent_kafka.Producer."""
    with patch("horizon_data_core.kafka_producer.Producer") as mock:
        yield mock


def test_kafka_producer_init(mock_confluent_producer):
    """Test KafkaProducer initialization with config."""
    producer = KafkaProducer("localhost:9092", "test.topic", acks="all", retries=5)

    # Verify confluent Producer was initialized with correct config
    mock_confluent_producer.assert_called_once()
    call_args = mock_confluent_producer.call_args[0][0]
    assert call_args["bootstrap.servers"] == "localhost:9092"
    assert call_args["acks"] == "all"
    assert call_args["retries"] == 5
    assert producer.topic == "test.topic"


def test_kafka_producer_init_minimal(mock_confluent_producer):
    """Test KafkaProducer initialization with minimal config."""
    producer = KafkaProducer("broker:9092", "my.topic")

    mock_confluent_producer.assert_called_once()
    call_args = mock_confluent_producer.call_args[0][0]
    assert call_args["bootstrap.servers"] == "broker:9092"
    assert producer.topic == "my.topic"


def test_kafka_producer_produce(mock_confluent_producer):
    """Test KafkaProducer.produce() sends message."""
    mock_producer_instance = Mock()
    mock_confluent_producer.return_value = mock_producer_instance

    producer = KafkaProducer("localhost:9092", "test.topic")
    key = b"test-key"
    value = b"test-value"

    producer.produce(key, value)

    # Verify produce was called with correct arguments
    mock_producer_instance.produce.assert_called_once_with(
        topic="test.topic", key=key, value=value, on_delivery=producer._delivery_callback
    )
    # Verify poll was called to trigger delivery reports
    mock_producer_instance.poll.assert_called_once_with(0)


def test_kafka_producer_produce_multiple(mock_confluent_producer):
    """Test multiple produce calls."""
    mock_producer_instance = Mock()
    mock_confluent_producer.return_value = mock_producer_instance

    producer = KafkaProducer("localhost:9092", "test.topic")

    for i in range(5):
        producer.produce(f"key-{i}".encode(), f"value-{i}".encode())

    assert mock_producer_instance.produce.call_count == 5
    assert mock_producer_instance.poll.call_count == 5


def test_kafka_producer_flush_success(mock_confluent_producer):
    """Test KafkaProducer.flush() waits for delivery."""
    mock_producer_instance = Mock()
    mock_producer_instance.flush.return_value = 0
    mock_confluent_producer.return_value = mock_producer_instance

    producer = KafkaProducer("localhost:9092", "test.topic")
    result = producer.flush(timeout=5.0)

    mock_producer_instance.flush.assert_called_once_with(5.0)
    assert result == 0


def test_kafka_producer_flush_with_remaining(mock_confluent_producer):
    """Test KafkaProducer.flush() returns remaining message count."""
    mock_producer_instance = Mock()
    mock_producer_instance.flush.return_value = 3  # 3 messages not delivered
    mock_confluent_producer.return_value = mock_producer_instance

    producer = KafkaProducer("localhost:9092", "test.topic")
    result = producer.flush(timeout=1.0)

    assert result == 3


def test_kafka_producer_close_all_delivered(mock_confluent_producer):
    """Test KafkaProducer.close() with all messages delivered."""
    mock_producer_instance = Mock()
    mock_producer_instance.flush.return_value = 0
    mock_confluent_producer.return_value = mock_producer_instance

    producer = KafkaProducer("localhost:9092", "test.topic")

    with patch("horizon_data_core.kafka_producer.logger") as mock_logger:
        producer.close()
        # Verify flush was called with 30s timeout
        mock_producer_instance.flush.assert_called_once_with(30.0)
        # Verify success log
        mock_logger.info.assert_called_with("All messages delivered successfully")


def test_kafka_producer_close_with_remaining_messages(mock_confluent_producer):
    """Test KafkaProducer.close() warns about undelivered messages."""
    mock_producer_instance = Mock()
    mock_producer_instance.flush.return_value = 5  # 5 messages remaining
    mock_confluent_producer.return_value = mock_producer_instance

    producer = KafkaProducer("localhost:9092", "test.topic")

    with patch("horizon_data_core.kafka_producer.logger") as mock_logger:
        producer.close()
        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        assert "5" in str(mock_logger.warning.call_args)


def test_kafka_producer_delivery_callback_success(mock_confluent_producer):
    """Test delivery callback logs success."""
    mock_producer_instance = Mock()
    mock_confluent_producer.return_value = mock_producer_instance

    producer = KafkaProducer("localhost:9092", "test.topic")

    mock_msg = Mock()
    mock_msg.topic.return_value = "test.topic"
    mock_msg.partition.return_value = 0
    mock_msg.offset.return_value = 42

    with patch("horizon_data_core.kafka_producer.logger") as mock_logger:
        producer._delivery_callback(None, mock_msg)
        mock_logger.debug.assert_called_once()
        # Verify debug message contains topic, partition, offset
        debug_msg = str(mock_logger.debug.call_args)
        assert "test.topic" in debug_msg
        assert "42" in debug_msg


def test_kafka_producer_delivery_callback_error(mock_confluent_producer):
    """Test delivery callback logs errors."""
    mock_producer_instance = Mock()
    mock_confluent_producer.return_value = mock_producer_instance

    producer = KafkaProducer("localhost:9092", "test.topic")

    mock_error = Mock()
    mock_error.__str__ = Mock(return_value="Connection timeout")
    mock_msg = Mock()

    with patch("horizon_data_core.kafka_producer.logger") as mock_logger:
        producer._delivery_callback(mock_error, mock_msg)
        mock_logger.error.assert_called_once()
        # Verify error message contains error details
        error_msg = str(mock_logger.error.call_args)
        assert "failed" in error_msg.lower()


def test_kafka_producer_produce_exception_handling(mock_confluent_producer):
    """Test produce() exception handling."""
    mock_producer_instance = Mock()
    mock_producer_instance.produce.side_effect = Exception("Broker unavailable")
    mock_confluent_producer.return_value = mock_producer_instance

    producer = KafkaProducer("localhost:9092", "test.topic")

    with pytest.raises(Exception, match="Broker unavailable"):
        producer.produce(b"key", b"value")


# =============================================================================
# Tests for KafkaConfig
# =============================================================================

from horizon_data_core.kafka_config import KafkaConfig


def test_kafka_config_to_confluent_config():
    """Test KafkaConfig.to_confluent_config() converts to confluent-kafka format."""
    config = KafkaConfig(
        bootstrap_servers="kafka:9092",
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-256",
        sasl_username="testuser",
        sasl_password="testpass",
        acks="all",
        retries=10,
        retry_backoff_ms=500,
        compression_type="lz4",
    )

    confluent_config = config.to_confluent_config()

    # Verify key transformation (underscores to dots)
    assert confluent_config["bootstrap.servers"] == "kafka:9092"
    assert confluent_config["security.protocol"] == "SASL_SSL"
    assert confluent_config["sasl.mechanism"] == "SCRAM-SHA-256"
    assert confluent_config["sasl.username"] == "testuser"
    assert confluent_config["sasl.password"] == "testpass"
    assert confluent_config["retry.backoff.ms"] == 500
    assert confluent_config["compression.type"] == "lz4"
    # Check production settings are included
    assert confluent_config["enable.idempotence"] is True
    assert confluent_config["max.in.flight.requests.per.connection"] == 5
