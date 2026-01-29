"""Thread-safe telemetry queue for buffering when collector is unreachable.

This module provides a bounded queue for storing telemetry data when the
OpenTelemetry collector is temporarily unavailable.
"""

import os
import pickle
import threading
from collections import deque
from typing import Any, List, Optional

from ..utils.exceptions import BufferingError


class TelemetryQueue:
    """Thread-safe bounded queue for telemetry buffering.

    Provides in-memory queueing with optional disk persistence for
    telemetry data when the collector is temporarily unreachable.

    Thread Safety:
        All operations are protected by a threading.Lock to ensure
        safe concurrent access from multiple threads.

    Examples:
        >>> queue = TelemetryQueue(max_size=1000)
        >>> queue.enqueue({"metric": "model.predictions_total", "value": 1})
        >>> batch = queue.dequeue_batch(size=10)
        >>> queue.size()
        0

        With disk persistence:
        >>> queue = TelemetryQueue(
        ...     max_size=1000,
        ...     persist=True,
        ...     persist_path="~/.mca_sdk/queue.pkl"
        ... )
    """

    def __init__(
        self, max_size: int = 1000, persist: bool = False, persist_path: Optional[str] = None
    ):
        """Initialize telemetry queue.

        Args:
            max_size: Maximum number of items in queue (default: 1000)
            persist: Whether to persist queue to disk (default: False)
            persist_path: Path for queue persistence (required if persist=True)

        Raises:
            BufferingError: If persist=True but persist_path not provided
        """
        if max_size <= 0:
            raise BufferingError(f"max_size must be positive, got {max_size}")

        self._max_size = max_size
        self._queue = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._persist = persist
        self._persist_path = persist_path

        # Validate persistence configuration
        if self._persist and not self._persist_path:
            raise BufferingError("persist_path required when persist=True")

        # Expand user path if provided
        if self._persist_path:
            self._persist_path = os.path.expanduser(self._persist_path)

        # Load persisted queue if enabled
        if self._persist:
            self._load_from_disk()

    def enqueue(self, item: Any) -> bool:
        """Add item to queue.

        Thread-safe operation that adds an item to the queue. If the queue
        is full, the oldest item is automatically evicted (FIFO).

        Args:
            item: Telemetry data to enqueue (any serializable object)

        Returns:
            True if item was added, False if queue is full and item was dropped

        Example:
            >>> queue.enqueue({"metric": "model.latency_seconds", "value": 0.15})
            True
        """
        with self._lock:
            was_full = len(self._queue) >= self._max_size

            # deque with maxlen automatically evicts oldest when full
            self._queue.append(item)

            # Persist to disk if enabled
            if self._persist:
                self._save_to_disk()

            return not was_full

    def dequeue(self) -> Optional[Any]:
        """Remove and return oldest item from queue.

        Thread-safe operation that removes the oldest item (FIFO).

        Returns:
            The oldest item in queue, or None if queue is empty

        Example:
            >>> item = queue.dequeue()
        """
        with self._lock:
            if not self._queue:
                return None

            item = self._queue.popleft()

            # Persist to disk if enabled
            if self._persist:
                self._save_to_disk()

            return item

    def dequeue_batch(self, size: int) -> List[Any]:
        """Remove and return multiple items from queue.

        Thread-safe operation that removes up to `size` oldest items (FIFO).

        Args:
            size: Maximum number of items to dequeue

        Returns:
            List of items (may be shorter than size if queue has fewer items)

        Example:
            >>> batch = queue.dequeue_batch(size=100)
            >>> len(batch)
            42  # Queue had only 42 items
        """
        with self._lock:
            batch = []
            for _ in range(min(size, len(self._queue))):
                if self._queue:
                    batch.append(self._queue.popleft())

            # Persist to disk if enabled and batch was dequeued
            if self._persist and batch:
                self._save_to_disk()

            return batch

    def peek(self) -> Optional[Any]:
        """View oldest item without removing it.

        Thread-safe operation that returns the oldest item without modification.

        Returns:
            The oldest item in queue, or None if queue is empty
        """
        with self._lock:
            if not self._queue:
                return None
            return self._queue[0]

    def size(self) -> int:
        """Get current queue size.

        Thread-safe operation that returns the number of items in queue.

        Returns:
            Current number of items in queue
        """
        with self._lock:
            return len(self._queue)

    def is_empty(self) -> bool:
        """Check if queue is empty.

        Thread-safe operation.

        Returns:
            True if queue is empty, False otherwise
        """
        with self._lock:
            return len(self._queue) == 0

    def is_full(self) -> bool:
        """Check if queue is at maximum capacity.

        Thread-safe operation.

        Returns:
            True if queue is full, False otherwise
        """
        with self._lock:
            return len(self._queue) >= self._max_size

    def clear(self) -> int:
        """Remove all items from queue.

        Thread-safe operation that empties the queue.

        Returns:
            Number of items that were removed

        Example:
            >>> removed = queue.clear()
            >>> print(f"Removed {removed} items")
        """
        with self._lock:
            count = len(self._queue)
            self._queue.clear()

            # Persist to disk if enabled
            if self._persist:
                self._save_to_disk()

            return count

    def _save_to_disk(self) -> None:
        """Persist queue to disk (internal method).

        SECURITY: Uses user-specific directory with restricted permissions.
        Creates parent directories if they don't exist.

        Raises:
            BufferingError: If disk write fails
        """
        if not self._persist_path:
            return

        try:
            # Create parent directory if it doesn't exist
            # SECURITY: Ensure directory has restricted permissions (0o700)
            parent_dir = os.path.dirname(self._persist_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, mode=0o700, exist_ok=True)

            # Write queue to disk with pickle
            # Use list() to create a snapshot of deque for serialization
            with open(self._persist_path, "wb") as f:
                pickle.dump(list(self._queue), f)

            # SECURITY: Set restrictive permissions on queue file
            os.chmod(self._persist_path, 0o600)

        except Exception:
            # Don't raise exception - disk persistence is best-effort
            # Log error but allow queue operations to continue
            pass

    def _load_from_disk(self) -> None:
        """Load persisted queue from disk (internal method).

        Called during initialization if persist=True and file exists.

        Raises:
            BufferingError: If disk read fails with corrupt data
        """
        if not self._persist_path or not os.path.exists(self._persist_path):
            return

        try:
            with open(self._persist_path, "rb") as f:
                items = pickle.load(f)

            # Validate loaded data
            if not isinstance(items, list):
                raise BufferingError("Persisted queue is not a list")

            # Restore queue (respecting max_size limit)
            self._queue = deque(items[-self._max_size :], maxlen=self._max_size)

        except Exception:
            # Corrupt or invalid persisted queue - start fresh
            # Don't raise exception to avoid blocking SDK initialization
            self._queue = deque(maxlen=self._max_size)
