"""Messaging configuration classes for DASF."""

# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import atexit
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from pydantic import Field, Json, PositiveInt, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from demessaging.utils import append_parameter_docs

if TYPE_CHECKING:
    from demessaging.messaging.producer import MessageProducer


@append_parameter_docs
class BaseMessagingConfig(BaseSettings):  # type: ignore
    """Base class for messaging configs."""

    model_config = SettingsConfigDict(env_prefix="de_backend_")

    topic: str = Field(
        description=(
            "The topic identifier under which to register at the pulsar."
        )
    )

    header: Union[Json[Dict[str, Any]], Dict[str, Any]] = Field(  # type: ignore
        default_factory=dict, description="Header parameters for the request"  # type: ignore[arg-type]
    )

    max_workers: Optional[PositiveInt] = Field(
        default=None,
        description=(
            "(optional) number of concurrent workers for handling requests, "
            "default: number of processors on the machine, multiplied by 5."
        ),
    )

    queue_size: Optional[PositiveInt] = Field(
        default=None,
        description=(
            "(optional) size of the request queue, if MAX_WORKERS is set, "
            "this needs to be at least as big as MAX_WORKERS, "
            "otherwise an AttributeException is raised."
        ),
    )

    max_payload_size: int = Field(
        default=500 * 1024,
        description=(
            "(optional) maximum payload size, must be smaller than pulsars 'webSocketMaxTextFrameSize', "
            "which is configured e.g.via 'pulsar/conf/standalone.conf'."
            "default: 512000 (500kb)."
        ),
    )

    producer_keep_alive: int = Field(
        default=120,
        description=(
            "The amount of time that the websocket connection to a producer "
            "should be kept open. By default, 2 minutes (120 seconds). On "
            "each outgoing message, the timer will be reset. Set this to 0 to "
            "immediately close the connection when a message has been sent "
            "and acknowledged."
        ),
    )

    producer_connection_timeout: int = Field(
        default=30,
        description=(
            "The amount of time that we grant producers to establish a "
            "connection to the message broker in order to send a response. If "
            "a connection cannot be established in this time, the response "
            "will not be sent and the connection will be closed."
        ),
    )

    _producer: Optional[MessageProducer] = None

    @property
    def producer(self) -> MessageProducer:
        """The connected producer for the messaging config"""
        from demessaging.messaging.producer import MessageProducer

        if self._producer:
            return self._producer
        else:
            self._producer = producer = MessageProducer(self)
            producer.connect()
            atexit.register(producer.disconnect)
            return producer

    @model_validator(mode="after")
    def validate_queue_size(self):
        """Check that the queue_size is smaller than the max_workers."""
        queue_size = self.queue_size
        max_workers = self.max_workers
        if queue_size is not None and max_workers is not None:
            if queue_size < max_workers:
                raise ValueError(
                    f"queue_size ({queue_size}) needs to be larger than or "
                    f"equal to max_workers ({max_workers})"
                )
        return self

    def get_topic_url(
        self, topic: str, subscription: Optional[str] = None
    ) -> str:
        """Build the URL to connect to a websocket."""
        raise NotImplementedError(
            "this method is supposed to be implemented by subclasses"
        )


@append_parameter_docs
class PulsarConfig(BaseMessagingConfig):
    """A configuration class to connect to the pulsar messaging framework."""

    host: str = Field(
        "localhost", description="The remote host of the pulsar."
    )

    port: str = Field(
        "8080", description="The port of the pulsar at the given :attr:`host`."
    )

    persistent: str = Field("non-persistent")

    tenant: str = Field("public")

    namespace: str = Field("default")

    def get_topic_url(
        self, topic: str, subscription: Optional[str] = None
    ) -> str:
        """Build the URL to connect to a websocket."""
        connection_type = "consumer" if subscription else "producer"
        sub = ("/" + subscription) if subscription else ""
        return (
            f"ws://{self.host}:{self.port}/ws/v2/{connection_type}/"
            f"{self.persistent}/{self.tenant}/{self.namespace}/{topic}{sub}"
        )


@append_parameter_docs
class WebsocketURLConfig(BaseMessagingConfig):
    """A configuration for a websocket."""

    websocket_url: str = Field(
        "", description="The fully qualified URL to the websocket."
    )

    producer_url: Optional[str] = Field(
        None,
        description=(
            "An alternative URL to use for producers. If None, the "
            "`websocket_url` will be used."
        ),
    )

    consumer_url: Optional[str] = Field(
        None,
        description=(
            "An alternative URL to use for consumers. If None, the "
            "`websocket_url` will be used."
        ),
    )

    def get_topic_url(
        self, topic: str, subscription: Optional[str] = None
    ) -> str:
        """Build the URL to connect to a websocket."""
        sub = ("/" + subscription) if subscription else ""
        if subscription:
            uri = self.consumer_url or self.websocket_url
        else:
            uri = self.producer_url or self.websocket_url
        if not uri.endswith("/"):
            uri += "/"
        return uri + topic + sub
