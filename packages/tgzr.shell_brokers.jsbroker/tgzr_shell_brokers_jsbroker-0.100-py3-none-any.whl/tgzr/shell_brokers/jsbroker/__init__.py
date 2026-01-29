from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Any

import logging

import nats
from nats.aio.client import Client as NatsClient
from nats.js import JetStreamContext

from tgzr.shell.broker import AsyncBroker, AsyncBrokerImplementation

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from nats.aio.subscription import Subscription as NatsSubscription


class JSBroker(AsyncBrokerImplementation):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._nc: NatsClient = None  # type: ignore
        self._js: JetStreamContext = None  # type: ignore

    def connected(self) -> bool:
        return self._nc is not None

    async def connect(self, config: dict[str, Any]):
        servers = config["servers"]
        user_credentials = config["user_credentials"]

        connection_name = "tgzr.shell.stream_broker"
        logger.info(
            f"+ Broker Connecting to {servers} using user credentials {user_credentials}"
        )
        logger.info(f"       Creds from:{user_credentials}")
        logger.info(f"      Client Name:{connection_name}")
        self._nc = await nats.connect(
            servers,
            user_credentials=user_credentials,
            name="tgzr.shell.stream_broker",
        )
        self._js = self._nc.jetstream()

    async def disconnect(self):
        if self._nc is not None:
            await self._nc.close()

    async def publish(self, subject: str, event: AsyncBroker.Event) -> None:
        return await self._nc.publish(subject, event.to_bytes())

    async def query(
        self, subject: str, event: AsyncBroker.Event, timeout: float = 0.5
    ) -> AsyncBroker.Event:
        msg = await self._nc.request(subject, event.to_bytes(), timeout=timeout)
        event = AsyncBroker.Event.from_bytes(msg.data)
        # print("[QUERY SENT]", query_name, kwargs, "@", subject, "->", msg, "->", event)
        return event

    async def subscribe(
        self, subject_pattern: str, callback: Callable[[AsyncBroker.Event], None]
    ) -> AsyncBroker.Subscription:
        async def cb(msg: Msg, callback=callback):
            event = AsyncBroker.Event.from_bytes(msg.data)
            await callback(event)

        sub = await self._nc.subscribe(subject_pattern, cb=cb)
        subscription = AsyncBroker.Subscription(
            subject_pattern=subject_pattern, callback=callback, private_data=sub
        )
        return subscription

    async def unsubscribe(self, subscription: AsyncBroker.Subscription) -> bool:
        try:
            sub: NatsSubscription = subscription.private_data  # type: ignore
            await sub.unsubscribe()
        except:
            return False
        return True
