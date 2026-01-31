# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Consumer for messages submitted via the message broker."""
from __future__ import annotations

import asyncio
import base64
import concurrent.futures
import json
import logging
import sys
import textwrap
import threading
import time
from datetime import datetime
from time import sleep
from typing import TYPE_CHECKING, Dict, List, Optional

import websocket

from demessaging.messaging.connection import WebsocketConnection
from demessaging.PulsarMessageConstants import MessageType, PropertyKeys

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from demessaging.backend.module import ModuleAPIModel
    from demessaging.config import BaseMessagingConfig

# patch the asyncio loop if we are on windows
# see https://github.com/tornadoweb/tornado/issues/2751
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class MessageConsumer(WebsocketConnection):
    """Consumer for messages submitted via the message broker."""

    RECONNECT_TIMEOUT_SLEEP = 10  # seconds
    SOCKET_PING_INTERVAL = 60  # 1min

    def __init__(
        self,
        pulsar_config: BaseMessagingConfig,
        handle_request,
        handle_response=None,
        module_info: Optional[dict] = None,
        api_info: Optional[ModuleAPIModel] = None,
    ):
        super().__init__(pulsar_config)
        pulsar_config = self.pulsar_config
        self.handle_request = handle_request
        self.handle_response = handle_response
        self.module_info = module_info
        self.api_info = api_info

        # init event loop
        self.loop = asyncio.get_event_loop()
        self.request_semaphore: Optional[threading.BoundedSemaphore] = None
        if pulsar_config.queue_size is not None:
            self.request_semaphore = threading.BoundedSemaphore(
                value=pulsar_config.queue_size
            )
        self.pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=pulsar_config.max_workers
        )

        self.max_payload_size = pulsar_config.max_payload_size
        self.connection_attempts = 0
        self.subscription = None
        self.producers: Dict[str, websocket.WebSocketApp] = {}
        self.producer_threads: Dict[
            websocket.WebSocketApp, threading.Thread
        ] = {}
        self.producer_locks: Dict[websocket.WebSocketApp, threading.Lock] = {}
        self.producer_timer: Dict[websocket.WebSocketApp, threading.Timer] = {}
        self.setup_subscription()

    def wait_for_websocket_connection(
        self, ws_app: websocket.WebSocketApp, timeout=10
    ):
        start = time.time()
        while (
            not (ws_app.sock and ws_app.sock.connected)
            and time.time() - start < timeout
        ):
            time.sleep(0.1)
        return ws_app.sock and ws_app.sock.connected

    def open_producer_app(self, topic, **kwargs):
        ws_app = self.create_websocketapp(
            topic=topic, on_message=self.on_producer_message, **kwargs
        )

        self.producer_threads[ws_app] = thread = threading.Thread(
            target=ws_app.run_forever,
            kwargs=dict(
                reconnect=self.RECONNECT_TIMEOUT_SLEEP,
                ping_interval=self.SOCKET_PING_INTERVAL,
            ),
            daemon=True,
        )
        thread.start()
        self.producer_locks[ws_app] = threading.Lock()
        self.reset_close_timer(ws_app)
        return ws_app

    def close_websocket_app(
        self, ws_app: websocket.WebSocketApp, reason: str = "unspecified"
    ):
        logger.info(
            "Closing producer connection to %s. Reason: %s", ws_app.url, reason
        )
        for topic, _ws_app in list(self.producers.items()):
            if _ws_app is ws_app:
                self.producers.pop(topic, None)
        ws_app.close()
        try:
            timer = self.producer_timer.pop(ws_app)
        except KeyError:
            pass
        else:
            timer.cancel()
        self.producer_threads.pop(ws_app, None)
        self.producer_locks.pop(ws_app, None)

    def reset_close_timer(self, ws_app: websocket.WebSocketApp):
        try:
            current_timer = self.producer_timer[ws_app]
        except KeyError:
            pass
        else:
            current_timer.cancel()
        if self.pulsar_config.producer_keep_alive:
            logger.debug(
                "Resetting producer websocket closing timer for %s", ws_app.url
            )
            keep_alive = self.pulsar_config.producer_keep_alive
            self.producer_timer[ws_app] = timer = threading.Timer(
                keep_alive,
                self.close_websocket_app,
                args=(ws_app, "no message since %s seconds" % keep_alive),
            )
            timer.start()

    def on_producer_message(self, ws_app: websocket.WebSocketApp, msg: str):
        # handle message acknowledgement for producer and reset timer
        ack = json.loads(msg)
        if ack["result"] != "ok":
            logger.error("Failed to send message: %s", ack)

        if not self.pulsar_config.producer_keep_alive:
            self.close_websocket_app(ws_app, "Response successfully sent.")

    def setup_subscription(self):
        # prepare timestamp string as part of subscription name
        timestr = datetime.now().isoformat()[:19]
        subscription_name = "backend-module-" + timestr

        self.connection_attempts += 1
        self.subscription = self.create_websocketapp(
            subscription=subscription_name,
            header=self.pulsar_config.header,
        )

    def disconnect(self):
        # close consumer
        if self.subscription is not None:
            try:
                self.subscription.close()
            except Exception:
                logger.error(
                    "Failed to close incoming websocket connection for consumer",
                    exc_info=True,
                )
            finally:
                self.subscription = None

        # close producers
        for ws_app in list(self.producers.values()):
            self.close_websocket_app(ws_app, "Disconnecting.")

    def wait_for_request(self):
        # register request event handler
        logger.info("waiting for incoming request")
        if self.subscription is None:
            self.setup_subscription()

        try:
            teardown = self.subscription.run_forever(
                ping_interval=self.SOCKET_PING_INTERVAL,
                reconnect=self.RECONNECT_TIMEOUT_SLEEP,
            )
        except Exception:
            logger.error("Exception occured in run_forever", exc_info=True)
            teardown = True
        finally:
            logger.info("Connection dropped with error: %s", teardown)
            if self.loop.is_running():
                self.loop.stop()
            self.disconnect()

    def on_message(self, ws_app: websocket.WebSocketApp, msg):
        # handle empty message
        if msg is None:
            logger.debug("empty message received")
            return

        # parse json message
        msg = json.loads(msg)

        # validate message
        # verify that we got a response_topic
        if MessageConsumer.is_valid_request(msg):
            # acknowledge request
            # FIXME: when do we actually acknowledge a message? right after receiving it or after processing it?
            self.acknowledge(msg)

            # handle according to message type
            msg_type = MessageConsumer.extract_message_type(msg)
            if msg_type == MessageType.PING:
                # simply reply with pong
                self.send_pong(msg)
            elif msg_type == MessageType.PONG:
                # handle pong message
                self.handle_pong(msg)
            elif msg_type == MessageType.INFO:
                # handle info message
                self.handle_info(msg)
            elif msg_type == MessageType.API_INFO:
                # handle API info message
                self.handle_api_info(msg)
            elif msg_type == MessageType.REQUEST:
                # handle request message later via event loop
                # self.loop.call_soon(self.handle_request, msg)
                if self.request_semaphore is None:
                    # no bounded queue - directly pass the request to the executor
                    self.loop.run_in_executor(
                        self.pool, self.handle_request, msg
                    )
                else:
                    # bounded queue size - check available space
                    if self.request_semaphore.acquire(blocking=False):
                        # there is still space in the queue - pass to executor queue
                        self.loop.run_in_executor(
                            self.pool, self.handle_request_via_queue, msg
                        )
                    else:
                        # queue is full - reject request
                        self.send_error(
                            request=msg,
                            error_message="request rejected due to queue overflow, try again later",
                        )

                # todo: do we need to address any exceptions here?? e.g. via future.add_done_callback()
                # Process(target=self.handle_request, args=(msg,)).start()
            elif msg_type == MessageType.RESPONSE:
                if self.handle_response:
                    # handle response message later via event loop
                    self.loop.call_soon(self.handle_response, msg)
                    # Process(target=self.handle_response, args=(msg,)).start()
                else:
                    logger.debug(
                        "ignoring response message due to missing handle_response function"
                    )
            else:
                logger.warning(
                    "received unsupported message type: " + msg_type
                )
        else:
            logger.warning(
                "message with unsupported structure received - ignoring it"
            )

    def handle_request_via_queue(self, msg):
        # here the semaphore has already been acquired
        try:
            self.handle_request(msg)
        finally:
            # no matter what - release the semaphore
            self.request_semaphore.release()

    def acknowledge(self, msg):
        self.subscription.sock.send(
            json.dumps({"messageId": msg["messageId"]})
        )

    def send_error(self, request, error_message):
        logger.info(
            "Sending error message to %s: %s",
            MessageConsumer.extract_response_topic(request),
            error_message,
        )
        self.send_response(
            request=request,
            response_payload=error_message,
            response_properties={"status": "error"},
        )

    def send_response(
        self,
        request,
        response_payload=None,
        msg_type=MessageType.RESPONSE,
        response_properties=None,
    ):
        if not MessageConsumer.is_valid_request(request):
            return

        # the request is valid - create a producer for the given response topic
        response_topic = MessageConsumer.extract_response_topic(request)

        if response_properties is None:
            response_properties = {}

        # prepare response
        response_properties[PropertyKeys.REQUEST_CONTEXT] = context = (
            MessageConsumer.extract_context(request)
        )
        response_properties[PropertyKeys.MESSAGE_TYPE] = msg_type
        response_properties[PropertyKeys.SOURCE_TOPIC] = (
            self.pulsar_config.topic
        )

        if response_topic in self.producers:
            # we already have a producer for this
            producer = self.producers[response_topic]
        else:
            # no producer yet, create one
            producer = self.open_producer_app(
                topic=response_topic, header=self.pulsar_config.header
            )
            self.producers[response_topic] = producer

        with self.producer_locks[producer]:
            is_connected = self.wait_for_websocket_connection(
                producer, self.pulsar_config.producer_connection_timeout
            )
            if not is_connected:
                logger.error(
                    "Failed to establish producer websocket connection to "
                    "topic %s within %s seconds. Stop sending response.",
                    response_topic,
                    self.pulsar_config.producer_connection_timeout,
                )
                self.close_websocket_app(
                    producer, "Failed to establish websocket connection."
                )
                return

            self.reset_close_timer(producer)

            # send the response
            msg = {
                "properties": response_properties,
                "context": str(context),
                "payload": "",
            }
            if response_payload:
                if isinstance(response_payload, str):
                    response_payload = response_payload.encode("utf-8")
                elif isinstance(response_payload, dict):
                    response_payload = json.dumps(response_payload).encode(
                        "utf-8"
                    )

                if len(response_payload) > self.max_payload_size:
                    logger.debug("sending fragmented message")
                    # the payload exceeds the maximum size - send fragmented message
                    payload_fragments: List[str] = textwrap.wrap(  # type: ignore
                        text=base64.b64encode(response_payload).decode(
                            "utf-8"
                        ),
                        width=self.max_payload_size,
                    )

                    num_fragments = len(payload_fragments)
                    for i in range(num_fragments):
                        fragment_props = response_properties.copy()
                        fragment_props[PropertyKeys.FRAGMENT] = i
                        fragment_props[PropertyKeys.NUM_FRAGMENTS] = (
                            num_fragments
                        )

                        fragmented_msg = {
                            "properties": fragment_props,
                            "payload": payload_fragments[i],
                            "context": str(context),
                        }
                        producer.send(json.dumps(fragmented_msg))

                        # sleep 100ms
                        sleep(0.05)

                    logger.debug("sent {} fragments".format(num_fragments))
                    return

                # send unfragmented message
                msg["payload"] = base64.b64encode(response_payload).decode(
                    "utf-8"
                )

            producer.send(json.dumps(msg))

    def send_pong(self, request):
        logger.debug(
            "Sending DASF pong to %s",
            MessageConsumer.extract_response_topic(request),
        )
        self.send_response(request=request, msg_type=MessageType.PONG)

    def handle_pong(self, request):
        logger.info("pong received {0}", request)

    def handle_info(self, info_request):
        # check for available module info
        if self.module_info is None:
            # no module info provided
            logger.debug("missing info")
            self.send_response(
                info_request,
                response_properties={
                    "info": "This module does not provide capability information."
                },
            )
            return

        logger.debug("sending info response...")
        self.send_response(
            request=info_request,
            response_properties={"info": json.dumps(self.module_info)},
        )

    def handle_api_info(self, api_info_request):
        """Show the api of the module."""
        if self.api_info is None:
            # no module info provided
            logger.debug("missing api info")
            self.send_response(
                api_info_request,
                response_properties={
                    "info": "This module does not provide api information."
                },
            )
            return

        logger.debug("sending api_info response...")
        self.send_response(
            request=api_info_request,
            response_properties={"api_info": self.api_info.model_dump_json()},
        )

    @staticmethod
    def extract_response_topic(msg):
        if PropertyKeys.RESPONSE_TOPIC in msg["properties"]:
            return msg["properties"][PropertyKeys.RESPONSE_TOPIC]
        else:
            return None

    @staticmethod
    def extract_context(msg) -> Optional[str]:
        if PropertyKeys.REQUEST_CONTEXT in msg["properties"]:
            return str(msg["properties"][PropertyKeys.REQUEST_CONTEXT])
        elif PropertyKeys.REQUEST_CONTEXT in msg:
            return str(msg[PropertyKeys.REQUEST_CONTEXT])
        else:
            return None

    @staticmethod
    def extract_message_type(msg):
        if PropertyKeys.MESSAGE_TYPE in msg["properties"]:
            return msg["properties"][PropertyKeys.MESSAGE_TYPE]
        else:
            return None

    @staticmethod
    def is_valid_value(value):
        return value is not None and isinstance(value, str) and len(value) > 0

    @staticmethod
    def is_valid_request(request_message):
        # for now the request is valid if we find a valid response topic, context and message type
        return (
            MessageConsumer.is_valid_value(
                MessageConsumer.extract_response_topic(request_message)
            )
            and MessageConsumer.is_valid_value(
                MessageConsumer.extract_context(request_message)
            )
            and MessageConsumer.is_valid_value(
                MessageConsumer.extract_message_type(request_message)
            )
        )
