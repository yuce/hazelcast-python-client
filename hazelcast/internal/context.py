from _contextvars import ContextVar

from hazelcast.internal.asyncio_util import AtomicInteger

LOCK_ID_GEN = AtomicInteger(1)
LOCK_VAR: ContextVar[int] = ContextVar("lock", default=0)


class LockID:

    def __init__(self):
        self.thread_id = LOCK_ID_GEN.get_and_increment()

    # def __enter__(self):
    #     self.token = LOCK_VAR.set(self.thread_id)
    #
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     LOCK_VAR.reset(self.token)

