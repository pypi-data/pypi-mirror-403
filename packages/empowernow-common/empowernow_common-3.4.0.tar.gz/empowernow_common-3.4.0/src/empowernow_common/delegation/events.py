"""Kafka event handlers for delegation cache invalidation.

This module provides event handling for delegation lifecycle events,
enabling cache invalidation across distributed services.

Event Contract:
    Topic: delegation.events
    Key: {delegator_arn}:{delegate_arn}

Event Types:
    - delegation.created: New delegation created
    - delegation.updated: Delegation modified (status, capabilities, expiry)
    - delegation.revoked: Delegation explicitly revoked
    - delegation.expired: Delegation TTL expired

Payload Schema:
    {
        "event_type": "delegation.updated",
        "event_id": "evt_abc123",
        "timestamp": "2026-01-09T12:00:00Z",
        "version": "1.0",
        "payload": {
            "delegation_id": "del_xyz789",
            "delegator_arn": "auth:user:entra:user123",
            "delegate_arn": "auth:agent:system:agent456",
            "changed_fields": ["status", "capability_ids"],
            "new_status": "revoked",
            "previous_status": "active"
        }
    }

Fallback Behavior:
    If Kafka is unavailable, TTL-only cache invalidation is used.
    The consumer continues running and reconnects automatically.

Usage:
    handler = DelegationEventHandler(l1_cache, l2_cache)

    # Handle single event
    await handler.handle_event(event)

    # Start consumer loop (blocks until stop() called)
    await handler.start_consumer_loop(kafka_consumer)
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, List, Optional, Protocol

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .cache import DelegationCache, RedisDelegationCache

logger = logging.getLogger(__name__)


# =============================================================================
# Event Types
# =============================================================================


class DelegationEventType(str, Enum):
    """Types of delegation lifecycle events."""

    CREATED = "delegation.created"
    """New delegation was created."""

    UPDATED = "delegation.updated"
    """Delegation was modified (status, capabilities, etc.)."""

    REVOKED = "delegation.revoked"
    """Delegation was explicitly revoked."""

    EXPIRED = "delegation.expired"
    """Delegation TTL expired."""


# =============================================================================
# Event Models
# =============================================================================


class DelegationEventPayload(BaseModel):
    """Payload for delegation events.

    Contains the identifiers needed for cache invalidation and
    optional context about what changed.
    """

    delegation_id: str = Field(..., description="ID of the affected delegation")
    delegator_arn: str = Field(..., description="ARN of the delegating user")
    delegate_arn: str = Field(..., description="ARN of the delegate agent")
    changed_fields: Optional[List[str]] = Field(
        None, description="Fields that changed (for update events)"
    )
    new_status: Optional[str] = Field(None, description="New status (if status changed)")
    previous_status: Optional[str] = Field(None, description="Previous status")


class DelegationEvent(BaseModel):
    """Delegation change event from Kafka.

    Full event envelope with metadata and payload.
    """

    event_type: DelegationEventType = Field(..., description="Type of event")
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="When the event occurred")
    version: str = Field(default="1.0", description="Event schema version")
    payload: DelegationEventPayload = Field(..., description="Event payload")


# =============================================================================
# Kafka Consumer Protocol
# =============================================================================


class KafkaConsumerProtocol(Protocol):
    """Protocol for Kafka consumer.

    Implement this to integrate with your Kafka client (e.g., aiokafka).
    """

    async def subscribe(self, topics: List[str]) -> None:
        """Subscribe to topics."""
        ...

    async def poll(self, timeout_ms: int = 1000) -> Optional[Any]:
        """Poll for next message."""
        ...

    async def commit(self) -> None:
        """Commit current offset."""
        ...


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class DelegationEventHandlerConfig:
    """Configuration for event handler.

    Attributes:
        topic: Kafka topic to consume from.
        consumer_group: Consumer group ID.
        poll_timeout_ms: Timeout for poll operations.
        max_lag_warning_seconds: Log warning if event lag exceeds this.
    """

    topic: str = "delegation.events"
    """Kafka topic for delegation events."""

    consumer_group: str = "delegation-cache-invalidator"
    """Kafka consumer group ID."""

    poll_timeout_ms: int = 1000
    """Timeout for poll operations in milliseconds."""

    max_lag_warning_seconds: float = 5.0
    """Log warning if event lag exceeds this threshold."""


# =============================================================================
# Event Handler
# =============================================================================


class DelegationEventHandler:
    """Handles delegation events from Kafka for cache invalidation.

    Eviction Strategy:
        On any delegation event, the handler invalidates:
        1. Primary cache key: {delegator_arn}|{delegate_arn}
        2. Both L1 (in-memory) and L2 (Redis) caches

    The handler monitors event lag and logs warnings if the consumer
    falls behind. TTL provides fallback consistency during lag.

    Example:
        handler = DelegationEventHandler(
            l1_cache=in_memory_cache,
            l2_cache=redis_cache,
            config=DelegationEventHandlerConfig(topic="delegation.events"),
        )

        # Handle single event (for testing)
        await handler.handle_event(event)

        # Start consumer loop
        asyncio.create_task(handler.start_consumer_loop(kafka_consumer))

        # Stop gracefully
        handler.stop()
    """

    def __init__(
        self,
        l1_cache: Optional["DelegationCache"],
        l2_cache: Optional["RedisDelegationCache"],
        config: Optional[DelegationEventHandlerConfig] = None,
    ) -> None:
        """Initialize event handler.

        Args:
            l1_cache: In-memory cache to invalidate (optional).
            l2_cache: Redis cache to invalidate (optional).
            config: Handler configuration.
        """
        self._l1_cache = l1_cache
        self._l2_cache = l2_cache
        self._config = config or DelegationEventHandlerConfig()
        self._running = False

    async def handle_event(self, event: DelegationEvent) -> int:
        """Handle a delegation event by invalidating caches.

        Args:
            event: The delegation event to handle.

        Returns:
            Number of cache entries invalidated.
        """
        payload = event.payload
        invalidated = 0

        logger.info(
            "Handling delegation event: type=%s, delegation_id=%s",
            event.event_type,
            payload.delegation_id,
        )

        # Check for lag
        now = datetime.now(timezone.utc)
        event_time = event.timestamp
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)

        lag = (now - event_time).total_seconds()
        if lag > self._config.max_lag_warning_seconds:
            logger.warning(
                "Delegation event lag: %.2fs > %.2fs threshold",
                lag,
                self._config.max_lag_warning_seconds,
            )

        # Invalidate L1 cache (in-memory)
        if self._l1_cache:
            try:
                if await self._l1_cache.invalidate(payload.delegator_arn, payload.delegate_arn):
                    invalidated += 1
            except Exception as e:
                logger.warning("L1 cache invalidation failed: %s", e)

        # Invalidate L2 cache (Redis)
        if self._l2_cache:
            try:
                if await self._l2_cache.invalidate(payload.delegator_arn, payload.delegate_arn):
                    invalidated += 1
            except Exception as e:
                logger.warning("L2 cache invalidation failed: %s", e)

        logger.debug(
            "Invalidated %d cache entries for event %s",
            invalidated,
            event.event_id,
        )
        return invalidated

    async def handle_raw_message(self, message_value: bytes) -> int:
        """Handle a raw Kafka message.

        Args:
            message_value: Raw message bytes from Kafka.

        Returns:
            Number of cache entries invalidated, or 0 on error.
        """
        try:
            data = json.loads(message_value)
            event = DelegationEvent.model_validate(data)
            return await self.handle_event(event)
        except json.JSONDecodeError as e:
            logger.error("Failed to decode delegation event JSON: %s", e)
            return 0
        except Exception as e:
            logger.error("Failed to handle delegation event: %s", e)
            return 0

    async def start_consumer_loop(self, consumer: KafkaConsumerProtocol) -> None:
        """Start the Kafka consumer loop.

        This runs until stop() is called. The loop handles errors gracefully
        and continues running to maintain cache invalidation.

        Args:
            consumer: Kafka consumer implementing KafkaConsumerProtocol.
        """
        await consumer.subscribe([self._config.topic])
        self._running = True

        logger.info(
            "Starting delegation event consumer on topic: %s",
            self._config.topic,
        )

        backoff_seconds = 0.25
        max_backoff_seconds = 30.0

        while self._running:
            try:
                message = await consumer.poll(timeout_ms=self._config.poll_timeout_ms)
                if message is not None:
                    await self.handle_raw_message(message.value)
                    await consumer.commit()
                # Reset backoff on successful poll (even if no message)
                backoff_seconds = 0.25
            except Exception as e:
                logger.error("Error in delegation event consumer loop: %s", e)
                # Exponential backoff to prevent log spam when Kafka is down
                await asyncio.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, max_backoff_seconds)
                # Continue running - TTL provides fallback

    def stop(self) -> None:
        """Stop the consumer loop gracefully."""
        self._running = False
        logger.info("Stopping delegation event consumer")

    @property
    def is_running(self) -> bool:
        """Check if the consumer loop is running."""
        return self._running


# =============================================================================
# Factory Function
# =============================================================================


def create_event_handler(
    l1_cache: Optional["DelegationCache"],
    l2_cache: Optional["RedisDelegationCache"],
    topic: str = "delegation.events",
) -> DelegationEventHandler:
    """Factory function to create an event handler.

    Args:
        l1_cache: In-memory cache (optional).
        l2_cache: Redis cache (optional).
        topic: Kafka topic to consume from.

    Returns:
        Configured DelegationEventHandler.
    """
    config = DelegationEventHandlerConfig(topic=topic)
    return DelegationEventHandler(l1_cache, l2_cache, config)


__all__ = [
    "DelegationEventType",
    "DelegationEventPayload",
    "DelegationEvent",
    "KafkaConsumerProtocol",
    "DelegationEventHandlerConfig",
    "DelegationEventHandler",
    "create_event_handler",
]
