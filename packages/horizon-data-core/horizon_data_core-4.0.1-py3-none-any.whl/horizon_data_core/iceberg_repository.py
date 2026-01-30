"""Iceberg repository with async write path for high-throughput data ingestion."""

from __future__ import annotations

import io
import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any

import pyarrow as pa
from pyarrow import ipc

from .base_types import PyarrowSerializable

if TYPE_CHECKING:
    import builtins

    from .kafka_producer import KafkaProducer
    from .schema_discovery import FieldIdMap, PartitionSpec

logger = logging.getLogger(__name__)


def _serialize_to_arrow_ipc(table: pa.Table) -> bytes:
    """Serialize a PyArrow Table to Arrow IPC stream format.

    This matches the format expected by horizon-iceberg-sink's decode_arrow_ipc.
    Handles tables with any number of batches correctly.

    Args:
        table: Arrow Table to serialize

    Returns:
        Arrow IPC stream format bytes
    """
    sink = io.BytesIO()
    with ipc.new_stream(sink, table.schema) as writer:
        for batch in table.to_batches():
            writer.write_batch(batch)
    return sink.getvalue()


class IcebergRepository[T: PyarrowSerializable]:
    """Repository for Iceberg tables with eventual consistency guarantees.

    This repository provides high-throughput write operations to Iceberg tables.
    Writes are asynchronous and eventually consistent - data is NOT immediately
    visible after insert() returns.

    **Consistency Model:**
    - Writes return immediately after queuing
    - Data becomes visible in Iceberg asynchronously
    - Exactly-once semantics guaranteed (no duplicates)

    **Latency Characteristics:**
    - **Low throughput**: 30-60 seconds
      - System waits to accumulate data for efficient storage
      - Optimizes for large, efficient Parquet files
    - **High throughput**: <1 second
      - Rapid data arrival triggers frequent flushes
      - Near real-time during heavy load

    **Use Cases:**
    - High-throughput streaming writes (IoT, telemetry, logs)
    - Analytics and batch workloads
    - Time-series data collection
    - Scenarios where eventual consistency is acceptable

    **Not Suitable For:**
    - Read-after-write consistency requirements
    - Transactional workflows requiring immediate visibility
    - Low-latency read-your-writes scenarios

    **Implementation Detail:**
    Internally, writes are sent to Kafka topics and consumed by the horizon-iceberg-sink
    service, which handles batching, sorting, and atomic commits to Iceberg with
    offset tracking for exactly-once semantics.

    Partition keys are dynamically computed from the Iceberg table's partition spec,
    discovered from the catalog at SDK initialization time. This ensures Kafka topic
    partitions align with Iceberg table partitions for optimal file layout.

    Example:
        >>> from kafka_producer import KafkaProducer
        >>> from schema_discovery import discover_field_ids, discover_partition_spec
        >>> producer = KafkaProducer("localhost:9092", "horizon.data_row")
        >>> field_ids = discover_field_ids("http://localhost:8181", "horizon.data_row")
        >>> partition_spec = discover_partition_spec("http://localhost:8181", "horizon.data_row")
        >>> repo = IcebergRepository[DataRow](producer, field_ids, partition_spec)
        >>>
        >>> # Write returns immediately, data visible after 30-60s
        >>> row = DataRow(data_stream_id=uuid4(), datetime=datetime.now(), ...)
        >>> repo.insert(row)
    """

    def __init__(self, producer: KafkaProducer, field_id_map: FieldIdMap, partition_spec: PartitionSpec) -> None:
        """Initialize the Iceberg repository.

        Args:
            producer: Kafka producer configured for the appropriate topic
            field_id_map: Mapping of column names to Iceberg field IDs from catalog
            partition_spec: Partition specification for computing Kafka keys
        """
        self.producer = producer
        self.field_id_map = field_id_map
        self.partition_spec = partition_spec
        logger.info(
            "Initialized IcebergRepository with async write path to topic=%s, field_ids=%s, partition_spec=%s",
            producer.topic,
            field_id_map,
            partition_spec,
        )

    def insert(self, model: T) -> T:
        """Insert a single record to Iceberg asynchronously.

        The record is queued for eventual write to Iceberg. This method returns
        immediately - the data is NOT visible in Iceberg until the async write
        completes (typically 30-60 seconds during low throughput).

        Args:
            model: PyarrowSerializable instance to insert

        Returns:
            The same model instance (unchanged)

        Raises:
            KafkaException: If message fails to be queued

        Note:
            Visibility latency depends on throughput. During high throughput periods,
            data may appear in <1 second. During quiet periods, expect 30-60 seconds.
        """
        # Serialize to Arrow IPC with field IDs from catalog
        arrow_table = model.to_pyarrow(self.field_id_map)
        payload = _serialize_to_arrow_ipc(arrow_table)

        # Compute partition key from the Iceberg partition spec
        model_data = model.model_dump(mode="python")
        key = self.partition_spec.compute_key(model_data)

        self.producer.produce(key, payload)
        return model

    def insert_batch(self, models: builtins.list[T]) -> builtins.list[T]:
        """Insert a batch of records to Iceberg asynchronously.

        More efficient than calling insert() multiple times when records share
        the same partition key. Records are grouped by key and each group is
        serialized and sent as one message.

        Args:
            models: List of PyarrowSerializable instances to insert

        Returns:
            The same model instances (unchanged)

        Raises:
            KafkaException: If message fails to be queued
            ValueError: If models list is empty

        Note:
            For optimal performance, batch sizes of 100-1000 records per partition
            are recommended. Records are automatically grouped by partition key to
            ensure proper Iceberg file layout.
        """
        if not models:
            return models

        # Group models by their partition key (computed from partition spec)
        groups: dict[bytes, list[T]] = defaultdict(list)
        for model in models:
            model_data = model.model_dump(mode="python")
            key = self.partition_spec.compute_key(model_data)
            groups[key].append(model)

        # Produce each group as a separate message
        for key, group_models in groups.items():
            # Combine all models in this group into a single Arrow table with field IDs from catalog
            arrow_tables = [model.to_pyarrow(self.field_id_map) for model in group_models]
            combined_table = pa.concat_tables(arrow_tables)

            # Serialize to Arrow IPC
            payload = _serialize_to_arrow_ipc(combined_table)

            self.producer.produce(key, payload)

        return models

    def upsert(self, model: T) -> T:
        """Upsert is not supported for Iceberg tables.

        Iceberg tables are append-only in this architecture. Use insert() instead.

        Args:
            model: Model instance

        Raises:
            NotImplementedError: Always raised
        """
        msg = "Upsert not supported for Iceberg tables (append-only). Use insert() instead."
        raise NotImplementedError(msg)

    def list(self, **filters: Any) -> builtins.list[T]:  # noqa: ANN401
        """List records from Iceberg table.

        Read operations are not currently supported through this repository.
        Use direct pyiceberg queries for reads.

        Args:
            **filters: Query filters (ignored)

        Raises:
            NotImplementedError: Always raised

        Note:
            Future versions may support reads via pyiceberg integration.
        """
        msg = "Read operations not supported. Use direct pyiceberg queries."
        raise NotImplementedError(msg)

    def get(self, **filters: Any) -> T | None:  # noqa: ANN401
        """Get a single record from Iceberg table.

        Read operations are not currently supported through this repository.
        Use direct pyiceberg queries for reads.

        Args:
            **filters: Query filters (ignored)

        Raises:
            NotImplementedError: Always raised
        """
        msg = "Read operations not supported. Use direct pyiceberg queries."
        raise NotImplementedError(msg)

    def flush(self, timeout: float = 10.0) -> int:
        """Wait for all pending messages to be acknowledged by Kafka broker.

        Provides synchronization point for pipeline checkpointing. Ensures messages
        produced BEFORE flush() are durable in Kafka before returning.

        Args:
            timeout: Maximum time to wait in seconds (default: 10.0)

        Returns:
            Number of messages still in queue (0 if all delivered successfully)

        Example - Checkpoint per file (at-least-once):
            >>> for file in files:
            ...     records = read_file(file)
            ...     repo.insert_batch(records)
            ...     if repo.flush(timeout=30.0) == 0:
            ...         checkpoint(file)  # Safe to mark as processed
            ...     # On crash: reprocess from checkpoint (may send duplicates)

        Example - Time-based checkpointing:
            >>> for record in stream:
            ...     repo.insert(record)
            ...     if time.time() - last_checkpoint > 10.0:
            ...         if repo.flush() == 0:
            ...             save_checkpoint(current_position)

        Guarantees:
            - Messages flushed successfully are durable in Kafka
            - Does NOT prevent duplicates on crash/retry (at-least-once)
            - Does NOT wait for Iceberg visibility (30-60s additional latency)
            - Horizon will render the most recent write in the case of a duplicate row
        """
        return self.producer.flush(timeout)
