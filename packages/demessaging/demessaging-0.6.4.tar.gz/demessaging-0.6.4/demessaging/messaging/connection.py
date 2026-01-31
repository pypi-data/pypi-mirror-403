# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Base module for a websocket connection."""
from __future__ import annotations

import logging
import random
import string
from abc import ABC
from typing import Optional

import websocket
from pydantic import validate_call

from demessaging import config


def get_random_letters(length: int) -> str:
    return "".join(random.choice(string.ascii_letters) for i in range(length))


logger = logging.getLogger(__name__)


class WebsocketConnection(ABC):
    """Base class to connect to a message broker using a websocket."""

    @validate_call
    def __init__(self, pulsar_config: config.BaseMessagingConfig):
        self.pulsar_config = pulsar_config

    def generate_response_topic(self, topic: Optional[str] = None) -> str:
        topic_name = topic or self.pulsar_config.topic or "anonymous"

        return topic_name + "_" + get_random_letters(8)

    def on_message(self, ws_app: websocket.WebSocketApp, msg):
        raise NotImplementedError

    def on_ping(self, ws_app: websocket.WebSocketApp, payload):
        logger.debug("pinged %s", ws_app.url)

    def on_pong(self, ws_app: websocket.WebSocketApp, payload):
        logger.debug("received pong from %s", ws_app.url)

    def on_close(
        self, ws_app: websocket.WebSocketApp, close_status_code, close_msg
    ):
        logger.debug(
            "Websocket connection to %s closed with status code %s, message %s.",
            ws_app.url,
            close_status_code,
            close_msg,
        )

    def create_websocketapp(
        self,
        subscription: Optional[str] = None,
        topic: Optional[str] = None,
        **app_kws,
    ) -> websocket.WebSocketApp:
        topic_name = topic or self.pulsar_config.topic

        topic_url = self.pulsar_config.get_topic_url(topic_name, subscription)

        app_kws.setdefault("on_message", self.on_message)
        app_kws.setdefault("on_ping", self.on_ping)
        app_kws.setdefault("on_pong", self.on_pong)
        app_kws.setdefault("on_close", self.on_close)

        logger.debug("Creating websocket connection for %s", topic_url)

        app = websocket.WebSocketApp(topic_url, **app_kws)

        return app

    def open_socket(
        self,
        subscription: Optional[str] = None,
        topic: Optional[str] = None,
        **connection_kws,
    ) -> websocket.WebSocket:
        topic_name = topic or self.pulsar_config.topic

        topic_url = self.pulsar_config.get_topic_url(topic_name, subscription)

        sock = websocket.create_connection(topic_url, **connection_kws)

        if sock:
            logger.debug("connection to {0} established".format(topic_url))

        return sock
