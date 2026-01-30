"""Kafka/Redpanda configuration for horizon-data-core."""

import logging
from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class StorageBackend(str, Enum):
    """Storage backend for data_row and metadata_row tables."""

    POSTGRES = "postgres"
    ICEBERG = "iceberg"  # Via Kafka -> horizon-iceberg-sink


class KafkaConfig(BaseSettings):
    """Configuration for Kafka/Redpanda connection.

    Configuration resolution order (lowest to highest precedence):
    1. Default values (defined in field definitions)
    2. Environment variables (RP_* prefix, loaded by dotenv-cli)
    3. Runtime values passed to __init__

    Example:
        # Load from environment (RP_BOOTSTRAP_SERVERS, etc.)
        config = KafkaConfig()

        # Override specific values at runtime
        config = KafkaConfig(bootstrap_servers="prod-kafka:9092")

    Note:
        Environment variables are loaded by dotenv-cli from hierarchical .env files
        before the Python process starts. This config class reads from those variables.
    """

    model_config = SettingsConfigDict(
        env_prefix="RP_",
        extra="ignore",
    )

    bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers (comma-separated)",
    )
    security_protocol: str = Field(
        default="SASL_SSL",
        description="Security protocol (PLAINTEXT, SASL_SSL, etc.)",
    )
    sasl_mechanism: str = Field(
        default="SCRAM-SHA-256",
        description="SASL mechanism for authentication",
    )
    sasl_username: str = Field(
        default="user",
        description="SASL username",
    )
    sasl_password: str = Field(
        default="password",
        description="SASL password",
    )
    acks: str = Field(
        default="all",
        description="Producer acks setting (all, 1, 0)",
    )
    retries: int = Field(
        default=5,
        description="Number of retries for failed sends",
    )
    retry_backoff_ms: int = Field(
        default=1000,
        description="Backoff time in ms between retries",
    )
    compression_type: str = Field(
        default="lz4",
        description="Compression type (none, gzip, snappy, lz4, zstd)",
    )

    # Topic configuration
    data_row_topic: str = Field(
        default="horizon.data_row",
        description="Kafka topic for data_row writes",
    )
    metadata_row_topic: str = Field(
        default="horizon.metadata_row",
        description="Kafka topic for metadata_row writes",
    )

    # Iceberg catalog configuration for schema discovery
    catalog_uri: str = Field(
        default="http://localhost:8181",
        description="REST catalog URI for Iceberg schema discovery",
    )
    catalog_warehouse: str | None = Field(
        default=None,
        description="Iceberg catalog warehouse location (optional)",
    )
    data_row_table: str = Field(
        default="horizon.data_row",
        description="Iceberg table name for data_row",
    )
    metadata_row_table: str = Field(
        default="horizon.metadata_row",
        description="Iceberg table name for metadata_row",
    )

    def to_confluent_config(self) -> dict[str, str | int]:
        """Convert to confluent-kafka producer configuration."""
        return {
            "bootstrap.servers": self.bootstrap_servers,
            "security.protocol": self.security_protocol,
            "sasl.mechanism": self.sasl_mechanism,
            "sasl.username": self.sasl_username,
            "sasl.password": self.sasl_password,
            "acks": self.acks,
            "retries": self.retries,
            "retry.backoff.ms": self.retry_backoff_ms,
            "compression.type": self.compression_type,
            # Additional production settings
            "enable.idempotence": True,  # Exactly-once semantics
            "max.in.flight.requests.per.connection": 5,
        }
