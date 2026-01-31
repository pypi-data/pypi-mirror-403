from __future__ import annotations
from typing import TYPE_CHECKING, Type, TypeVar, Callable, Awaitable, Any, DefaultDict

import dataclasses
import uuid
import json
import logging

from tgzr.package_management.plugin_manager import PluginManager, Plugin

if TYPE_CHECKING:
    from .session import Session

logger = logging.getLogger(__name__)

# class BrokerImplementation:

#     def __init__(self, broker: Broker):
#         self._broker = broker

#     def publish(self, topic: str, event: Broker.Event) -> None: ...
#     def subscribe(
#         self, topic_pattern: str, callback: EventCallbackType
#     ) -> Broker.Subscription: ...
#     def unsubscribe(self, subscription: Broker.Subscription) -> bool: ...


# class TestBroker(BrokerImplementation):
#     def __init__(self, broker: Broker):
#         super().__init__(broker=broker)
#         self._subscriptions: DefaultDict[str, list[Broker.Subscription]] = defaultdict(
#             list
#         )

#     def topic_match(self, topic: str, topic_pattern: str):
#         # TODO: implement it like nats or zenoh
#         return fnmatch.fnmatch(topic, topic_pattern)

#     def publish(self, topic: str, event: Broker.Event) -> None:
#         print("Publish", repr(topic), event)
#         for topic_pattern, subscriptions in self._subscriptions.items():
#             # print("?? topic match?", topic_pattern)
#             if self.topic_match(topic, topic_pattern):
#                 for subscription in subscriptions:
#                     print(
#                         f"  --push--> event to {subscription.topic_pattern!r}: {subscription.callback}"
#                     )
#                     subscription.callback(event)

#     def subscribe(
#         self, topic_pattern: str, callback: EventCallbackType
#     ) -> Broker.Subscription:
#         subscription = self._broker.Subscription(
#             topic_pattern=topic_pattern,
#             callback=callback,
#         )
#         self._subscriptions[topic_pattern].append(subscription)
#         return subscription

#     def unsubscribe(
#         self, subscription: Broker.Subscription, raise_if_unknown: bool = True
#     ) -> bool:
#         topic_pattern = subscription.topic_pattern
#         subscriptions = self._subscriptions[topic_pattern]
#         try:
#             subscriptions.remove(subscription)
#         except ValueError:
#             if not raise_if_unknown:
#                 return False
#             raise ValueError(f"This subscription is not registerd here: {subscription}")
#         return True


# class Broker:

#     class Event:
#         def __init__(self, **data: Any):
#             self._data = data

#         def __str__(self) -> str:
#             kwargs = ", ".join([f"{k}={v!r}" for k, v in self._data.items()])
#             return f"{self.__class__.__name__}({kwargs})"

#         def unpack(self, *args):
#             data = self._data.copy()
#             ret = []
#             for name in args:
#                 try:
#                     ret.append(data.pop(name))
#                 except KeyError:
#                     raise KeyError(
#                         f"Cannot unpack {args} from {self._data}, missing {name!r}."
#                     )
#             ret.append(data)
#             return ret

#     @dataclasses.dataclass
#     class Subscription:
#         topic_pattern: str
#         callback: Callable[[Broker.Event], None]
#         uuid: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)

#     def __init__(self, session: Session):
#         self._session = session
#         self._broker_implementation = self._create_broker_implementation()

#     def _create_broker_implementation(self) -> BrokerImplementation:
#         # TODO: select the Broker class from self.session.config
#         broker_implementation = TestBroker(self)
#         return broker_implementation

#     def publish(self, topic: str, **data: Any) -> None:
#         self._broker_implementation.publish(topic, self.Event(**data))

#     def cmd(self, cmd_name: str, **kwargs) -> None:
#         topic = "$CMD." + cmd_name
#         event = self.Event(**kwargs)
#         self._broker_implementation.publish(topic, event=event)

#     def subscribe(
#         self, topic_pattern: str, callback: EventCallbackType
#     ) -> Broker.Subscription:
#         return self._broker_implementation.subscribe(
#             topic_pattern=topic_pattern, callback=callback
#         )

#     def unsubscribe(self, subscription: Broker.Subscription) -> bool:
#         return self._broker_implementation.unsubscribe(subscription=subscription)


class AsyncBrokerImplementation(Plugin):

    @classmethod
    def plugin_type_name(cls) -> str:
        return "AsyncBrokerImplementation"

    async def connect(self, config: dict[str, Any]): ...
    def connected(self) -> bool: ...
    async def disconnect(self): ...
    async def publish(self, subject: str, event: AsyncBroker.Event) -> None: ...
    async def query(
        self, subject: str, event: AsyncBroker.Event, timeout: float = 0.5
    ) -> AsyncBroker.Event: ...
    async def subscribe(
        self,
        subject_pattern: str,
        callback: Callable[[AsyncBroker.Event], Awaitable[None]],
    ) -> AsyncBroker.Subscription: ...
    async def unsubscribe(self, subscription: AsyncBroker.Subscription) -> bool: ...


class BrokerPluginsManager(PluginManager[AsyncBrokerImplementation]):
    EP_GROUP = "tgzr.shell.broker_plugin"


EventType = TypeVar("EventType", bound="AsyncBroker.Event")


class AsyncBroker:
    class ExtendedJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, uuid.UUID):
                return str(obj)
            return json.JSONEncoder.default(self, obj)

    class Event:
        @classmethod
        def from_bytes(cls: Type[EventType], data: bytes) -> EventType:
            py_data = json.loads(data.decode())
            event = cls(py_data)
            return event

        def __init__(self, data: Any):
            self._data = data

        def __str__(self) -> str:
            # kwargs = ", ".join([f"{k}={v!r}" for k, v in self._data.items()])
            # return f"{self.__class__.__name__}({kwargs})"
            return f"{self.__class__.__name__}({self._data!r})"

        @property
        def data(self) -> Any:
            return self._data

        def unpack(self, *args):
            data = self._data.copy()
            ret = []
            for name in args:
                try:
                    ret.append(data.pop(name))
                except KeyError:
                    raise KeyError(
                        f"Cannot unpack {args} from {self._data}, missing {name!r}."
                    )
            ret.append(data)
            return ret

        def to_bytes(self) -> bytes:
            return json.dumps(self._data, cls=AsyncBroker.ExtendedJSONEncoder).encode()

    @dataclasses.dataclass
    class Subscription:
        subject_pattern: str
        callback: Callable[[AsyncBroker.Event], None]
        uuid: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)
        private_data: Any | None = None

    def __init__(self, session: Session):
        self._plugin_manager = BrokerPluginsManager()

        self._session = session
        self._broker_implementation = self._create_broker_implementation()

    def _create_broker_implementation(self) -> AsyncBrokerImplementation:
        broker_plugin_name = "tgzr.shell_brokers.jsbroker.JSBroker"
        async_broker_implementation = self._plugin_manager.get_plugin(
            broker_plugin_name
        )
        return async_broker_implementation

    def connected(self) -> bool:
        return self._broker_implementation.connected()

    async def connect(self, config: dict[str, Any]):
        await self._broker_implementation.connect(config)

    async def disconnect(self):
        await self._broker_implementation.disconnect()

    async def publish(self, subject: str, **data: Any) -> None:
        await self._broker_implementation.publish(subject, self.Event(data))

    # async def request(
    #     self, subject: str, event: AsyncBroker.Event, timeout: float = 0.5
    # ) -> Any:
    #     await self._broker_implementation.request(subject, event, timeout)

    async def cmd(self, service_name: str, cmd_name: str, **kwargs) -> None:
        subject = service_name + ".$CMD." + cmd_name
        event = self.Event(kwargs)
        await self._broker_implementation.publish(subject, event=event)

    async def query(
        self, service_name: str, query_name: str, timeout: float = 0.5, **kwargs
    ) -> None:
        subject = service_name + ".$QUERY." + query_name
        event = self.Event(kwargs)
        logger.debug(f"[SENDING QUERY] {subject=}, {event=}, {timeout=}")
        event = await self._broker_implementation.query(
            subject, event=event, timeout=timeout
        )
        logger.debug(f"[QUERY SENT] {query_name}, {kwargs} @ {subject} -> {event}")
        return event.data

    async def subscribe(
        self,
        subject_pattern: str,
        callback: Callable[[AsyncBroker.Event], Awaitable[None]],
    ) -> AsyncBroker.Subscription:
        return await self._broker_implementation.subscribe(
            subject_pattern=subject_pattern, callback=callback
        )

    async def unsubscribe(self, subscription: AsyncBroker.Subscription) -> bool:
        return await self._broker_implementation.unsubscribe(subscription=subscription)


# def test():
#     from .session import get_default_session
#     import os

#     os.environ["tgzr_home"] = "/home/dee/DEV/_OPEN-TGZR_/TGZR"
#     session = get_default_session(ensure_set=True)
#     if session is None:
#         raise Exception("No session!")
#     print(session.broker._broker_implementation)


# if __name__ == "__main__":
#     test()
