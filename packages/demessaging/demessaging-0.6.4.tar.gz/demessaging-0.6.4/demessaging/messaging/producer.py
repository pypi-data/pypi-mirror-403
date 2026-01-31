# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Producer of messages submitted for the message broker."""
from __future__ import annotations

import atexit
import base64
import json
import logging
import queue
import threading
import time
from datetime import datetime
from itertools import count
from typing import TYPE_CHECKING, Any, Dict, Optional

from deprogressapi import BaseReport
from websocket import WebSocketApp

from demessaging.messaging.connection import WebsocketConnection
from demessaging.PulsarMessageConstants import (
    MessageType,
    PropertyKeys,
    Status,
)

if TYPE_CHECKING:
    from demessaging.config import BaseMessagingConfig


logger = logging.getLogger(__name__)


class MessageProducer(WebsocketConnection):
    """Producer class to send requests to a registered backend module (topic)"""

    SOCKET_PING_INTERVAL = 60  # 1min
    RECONNECT_TIMEOUT_SLEEP = 5  # seconds

    out_app: WebSocketApp
    in_app: WebSocketApp

    def __init__(
        self, pulsar_config: BaseMessagingConfig, topic: Optional[str] = None
    ):
        super().__init__(pulsar_config)
        self.subscription_name: str = (
            "python-backend-" + datetime.now().isoformat()
        )
        self.context_counter = count()
        self._message_queues: Dict[int, queue.Queue] = {}

        # establish connections
        out_topic = self.pulsar_config.topic
        # topic override if given
        if topic is not None:
            out_topic = topic
        self.response_topic: str = self.generate_response_topic()
        self.out_topic = out_topic
        self.setup_subscription()

    def setup_subscription(self):
        self.out_app = self.create_websocketapp(
            topic=self.out_topic,
            header=self.pulsar_config.header,
            on_message=self.on_out_message,
        )
        # To be thread safe, we generate the response topic here
        self.in_app = self.create_websocketapp(
            subscription=self.subscription_name,
            topic=self.response_topic,
            header=self.pulsar_config.header,
            on_message=self.on_in_message,
        )

    def connect(self):
        self.out_app_thread = threading.Thread(
            target=self.out_app.run_forever,
            kwargs=dict(
                reconnect=self.RECONNECT_TIMEOUT_SLEEP,
                ping_interval=self.SOCKET_PING_INTERVAL,
            ),
            daemon=True,
        )
        self.in_app_thread = threading.Thread(
            target=self.in_app.run_forever,
            kwargs=dict(
                reconnect=self.RECONNECT_TIMEOUT_SLEEP,
                ping_interval=self.SOCKET_PING_INTERVAL,
            ),
            daemon=True,
        )
        self.out_app_thread.start()
        self.in_app_thread.start()
        atexit.register(self.disconnect)

    @property
    def is_connected(self) -> bool:
        """Check if the websocket apps are connected."""
        return bool(
            self.out_app.sock
            and self.out_app.sock.connected
            and self.in_app.sock
            and self.in_app.sock.connected
        )

    def wait_for_connection(self, timeout=10):
        """Wait until the websockets are connected"""
        start = time.time()
        while not self.is_connected and time.time() - start < timeout:
            time.sleep(0.1)
        return self.is_connected

    def on_out_message(self, ws_app: WebSocketApp, ack):
        """Message handler for the outgoing websocket connection."""
        # here we only expect acknowledgement messages.

        ack = json.loads(ack)
        if "context" in ack and "result" in ack:
            if "error" in ack["result"]:
                self._message_queues[int(ack["context"])].put_nowait(
                    {
                        "status": "error",
                        "error": "error sending the request",
                        "msg": ack,
                    }
                )
        else:
            logger.error("Invalid message from outgoing websocket: %s", ack)

    def on_in_message(self, ws_app: WebSocketApp, response):
        """Message handler for the incoming websocket connection."""
        # parse json message
        response = json.loads(response)
        props = response["properties"]

        # acknowledge the response
        self.in_app.send(json.dumps({"messageId": response["messageId"]}))

        # mapping from ids to existing reports
        reports: Dict[str, BaseReport] = {}

        if props[PropertyKeys.MESSAGE_TYPE] == MessageType.PROGRESS:
            # we received a progress report - print and ignore
            # decode progress data
            progress_data = base64.b64decode(response["payload"]).decode(
                "utf-8"
            )

            report = BaseReport.from_payload(progress_data)
            if report.report_id in reports:
                base_report = reports[report.report_id]
                for field in report.model_fields:
                    setattr(base_report, field, getattr(report, field))
            else:
                reports[report.report_id] = base_report = report
            if base_report.status != Status.RUNNING:
                base_report.complete(base_report.status)
            else:
                base_report.submit()
            return

        # assert that we received a 'response' message and check for matching context
        if props[PropertyKeys.MESSAGE_TYPE] != MessageType.RESPONSE:
            msg = {
                "status": "error",
                "error": "received message is not a response to the sent request",
                "msg": response,
            }
        elif "info" in props:
            msg = {
                "status": props.get("status", "success"),
                "msg": props["info"],
            }
        elif "api_info" in props:
            msg = {
                "status": props.get("status", "success"),
                "msg": props["api_info"],
            }
        elif "payload" in response:
            status = "success"
            if "status" in props:
                # we might successfully get a response, but it might contain an error from the backend
                status = props["status"]

            # decode b64 payload msg
            payload: str = response["payload"]

            try:
                payload = base64.b64decode(payload).decode("utf-8")
            except Exception as e:
                status = "error"
                payload = "error decoding payload: {0}".format(e)

            if status == "error":
                msg = {
                    "status": "error",
                    "error": payload,
                    "msg": response,
                }
            else:
                msg = {"status": status, "msg": payload}
        else:
            msg = {
                "status": "error",
                "error": "missing response payload",
                "msg": response,
            }
        context = int(props[PropertyKeys.REQUEST_CONTEXT])
        self._message_queues[context].put_nowait(msg)

    async def send_request(self, request_msg) -> Any:
        """Sends the given request to the backend module bound to the topic provided in the pulsar configuration.
        In order to increase re-usability the destination topic can be overridden with the optional topic argument.

        :param request_msg: dictionary providing a 'property' dictionary, a payload string, or both
        :param topic: overrides the used topic for this request
        :return: received response from the backend module
        """
        if not self.is_connected:
            connected = self.wait_for_connection()
            if not connected:
                raise ValueError(
                    "No websocket connection has been established!"
                )
        # create message context (from counter)
        context = next(self.context_counter)
        request_msg["context"] = context
        if "properties" not in request_msg:
            request_msg["properties"] = {}
        request_msg["properties"][
            PropertyKeys.RESPONSE_TOPIC
        ] = self.response_topic
        request_msg["properties"][PropertyKeys.REQUEST_CONTEXT] = request_msg[
            "context"
        ]
        request_msg["properties"].setdefault(
            PropertyKeys.MESSAGE_TYPE, MessageType.REQUEST
        )

        q = self._message_queues[context] = queue.Queue()

        # send message via outgoing connection to request topic
        self.out_app.send(json.dumps(request_msg))

        # wait for the response. In order to be able to use a keyboard
        # interrupt here, we are using timeouts of 1ms
        logger.info("start waiting for message")
        while True:
            try:
                return q.get(timeout=1)  # Allow check for Ctrl-C every second
            except queue.Empty:
                pass

    def disconnect(self):
        """Disconnect in- and out-sockets."""
        if hasattr(self, "in_app"):
            try:
                self.in_app.close()
            except Exception:
                logger.error(
                    "Failed to close incoming websocket connection for producer",
                    exc_info=True,
                )
            finally:
                del self.in_app

        if hasattr(self, "in_app"):
            try:
                self.out_app.close()
            except Exception:
                logger.error(
                    "Failed to close outgoing websocket connection for producer",
                    exc_info=True,
                )
            finally:
                del self.out_app
