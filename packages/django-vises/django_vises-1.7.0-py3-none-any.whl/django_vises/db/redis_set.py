from collections.abc import Iterable, MutableSet
from uuid import UUID

import redis

# https://redis.io/docs/latest/commands/sadd/

_REDIS_URI = "redis://localhost:6379/0"
_REDIS_SET_NAME = "set_name"


class RedisMutableSetAbc(MutableSet):

    def __init__(
        self,
        iterable=(),
        clear: bool = True,
        redis_uri: str = _REDIS_URI,
        redis_set_name: str = _REDIS_SET_NAME,
    ):
        self._conn = redis.from_url(url=redis_uri)
        self.name = redis_set_name

        if clear:
            self.clear()

        if iterable:
            for value in iterable:
                self.add(value)

    # redis interface
    def _add(self, item: str):
        self._conn.sadd(self.name, item)

    def _discard(self, item: str):
        self._conn.srem(self.name, item)

    def _sismember(self, item: str) -> bool:
        if self._conn.sismember(self.name, item) == 1:
            return True

        return False

    def _all(self) -> set[bytes]:
        # 异步模式下，返回的是 collections.abc.Awaitable[set[bytes]]
        return self._conn.smembers(self.name)  # type: ignore

    # set methods
    def __len__(self):  # type: ignore
        # 异步模式下，返回的是 Awaitable[int]
        return self._conn.scard(self.name)

    def add(self, value):
        raise NotImplementedError  # pragma: no cover

    def clear(self):
        self._conn.delete(self.name)


class RedisSetStr(RedisMutableSetAbc):
    def add(self, value: str):
        if not isinstance(value, str):
            raise TypeError

        super()._add(value)

    def discard(self, value: str):
        super()._discard(value)

    def __contains__(self, item):
        return self._sismember(item)

    def __iter__(self) -> Iterable[str]:  # type: ignore
        return iter(item.decode("utf-8") for item in self._all())

    def __repr__(self):
        return ", ".join([item.decode("utf-8") for item in self._all()])


class RedisSetInt(RedisMutableSetAbc):
    def add(self, value: int):
        if not isinstance(value, int):
            raise TypeError

        super()._add(str(value))

    def discard(self, value: int):
        super()._discard(str(value))

    def __contains__(self, item):
        return self._sismember(str(item))

    def __iter__(self) -> Iterable[int]:  # type: ignore
        return iter(int(item) for item in super()._all())

    def __repr__(self):
        return ", ".join([item.decode("utf-8") for item in self._all()])


class RedisSetUUID(RedisMutableSetAbc):
    def add(self, value: UUID):
        if not isinstance(value, UUID):
            raise TypeError

        super()._add(value.hex)

    def discard(self, value: UUID):
        super()._discard(value.hex)

    def __contains__(self, value):
        return self._sismember(value.hex)

    def __iter__(self) -> Iterable[UUID]:  # type: ignore
        return iter(UUID(item.decode("utf-8")) for item in super()._all())

    def __repr__(self):
        return ", ".join([str(UUID(item.decode("utf-8"))) for item in self._all()])
