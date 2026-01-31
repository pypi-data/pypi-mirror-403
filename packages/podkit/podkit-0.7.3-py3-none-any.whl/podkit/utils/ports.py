"""Port pool utility for dynamic port allocation."""

from threading import Lock


class PortPool:
    """Thread-safe port pool for container port allocation.

    Manages a pool of ports that can be allocated to containers and released
    back to the pool when containers are removed.

    Example:
        >>> pool = PortPool(start=5000, end=5999, ports_per_container=5)
        >>> ports = pool.allocate()
        >>> print(ports)
        [5000, 5001, 5002, 5003, 5004]
        >>> pool.release(ports)
    """

    def __init__(
        self,
        start: int = 5000,
        end: int = 5999,
        ports_per_container: int = 5,
    ):
        """Initialize port pool.

        Args:
            start: First port in range (inclusive). Default: 5000.
            end: Last port in range (inclusive). Default: 5999.
            ports_per_container: Number of ports to allocate per container. Default: 5.
        """
        self.start = start
        self.end = end
        self.ports_per_container = ports_per_container
        self.available: set[int] = set(range(start, end + 1))
        self.allocated: set[int] = set()
        self.lock = Lock()

    def allocate(self, count: int | None = None) -> list[int]:
        """Allocate ports from the pool.

        Args:
            count: Number of ports to allocate. If None, uses ports_per_container.

        Returns:
            List of allocated port numbers (sorted).

        Raises:
            RuntimeError: If not enough ports are available.
        """
        if count is None:
            count = self.ports_per_container

        with self.lock:
            if len(self.available) < count:
                raise RuntimeError(f"Not enough ports available: requested {count}, available {len(self.available)}")

            # Take lowest available ports for predictability
            ports = sorted(self.available)[:count]

            for port in ports:
                self.available.remove(port)
                self.allocated.add(port)

            return ports

    def release(self, ports: list[int]) -> None:
        """Release ports back to the pool.

        Args:
            ports: List of ports to release. Ports not from this pool are ignored.
        """
        with self.lock:
            for port in ports:
                if port in self.allocated:
                    self.allocated.remove(port)
                    self.available.add(port)

    @property
    def available_count(self) -> int:
        """Number of available ports."""
        with self.lock:
            return len(self.available)

    @property
    def allocated_count(self) -> int:
        """Number of allocated ports."""
        with self.lock:
            return len(self.allocated)
