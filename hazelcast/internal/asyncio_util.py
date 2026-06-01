import itertools


class AtomicInteger:
    """An Integer which can work atomically."""

    def __init__(self, start: int = 0):
        self._counter = itertools.count(start)

    def get_and_increment(self) -> int:
        """Returns the current value and increment it.

        Returns:
            Current value of AtomicInteger.
        """
        return next(self._counter)
