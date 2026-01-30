#  Copyright (C) 2025 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""Base class for ZMQ subscribers"""

import asyncio
import logging
from concurrent.futures import CancelledError
from contextlib import suppress
from datetime import datetime
from threading import Thread
from typing import Any

import zmq
import zmq.asyncio
from zmq.utils.monitor import recv_monitor_message

logger = logging.getLogger()

__all__ = ["ZeroMQSubscriber", "AsyncZeroMQSubscriber"]


class ZeroMQSubscriber:
    """Base class for ZMQ subscribers. Usage:

    with ZeroMQSubscriber("tcp://host:port", ["topic"]) as subscriber:
        (topic, timestamp, message) = subscriber.recv()
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, connect_uri: str, topics: list[bytes | str]):
        """

        param connect_uri: uri of pattern protocol://fqdn:port
        param topics: List of topics to subscribe to, must be bytearray use str.encode()
        """
        self._ctx = self._new_zmq_context()
        self._subscriber = self._ctx.socket(zmq.SUB)
        self._thread = None

        self._connect_uri = connect_uri
        self.nr_connects = 0
        self.nr_disconnects = 0
        self.is_connected = False

        if isinstance(topics, list) and all(isinstance(y, str) for y in topics):
            self._topics = [topic.encode() for topic in topics]
        else:
            self._topics = topics

        # create monitoring socket to catch all events from the start
        self.monitor = self._subscriber.get_monitor_socket()

        # subscribe
        self._subscriber.connect(connect_uri)
        for topic in self._topics:
            self._subscriber.setsockopt(zmq.SUBSCRIBE, topic)

    @staticmethod
    def _new_zmq_context():
        """Return a new ZMQ Context"""
        return zmq.Context.instance()

    def __repr__(self):
        return f"{self.__class__.__name__}({self._connect_uri}, {self._topics})"

    def _handle_event(self, evt: dict[str, Any]):
        """Process a single monitor event."""

        if evt["event"] == zmq.EVENT_HANDSHAKE_SUCCEEDED:
            logger.info("ZeroMQ connected: %s", self)
            self.nr_connects += 1
            self.is_connected = True
        elif evt["event"] == zmq.EVENT_DISCONNECTED:
            logger.warning("ZeroMQ disconnected: %s", self)
            self.nr_disconnects += 1
            self.is_connected = False

    def _event_monitor_thread(self):
        """Thread running the event monitor."""

        logger.info("ZeroMQ event monitor started: %s", self)

        try:
            while self.monitor.poll():
                evt = recv_monitor_message(self.monitor)
                if evt["event"] == zmq.EVENT_MONITOR_STOPPED:
                    break

                self._handle_event(evt)
        except Exception:
            logger.exception("Error in ZeroMQ event monitor: %s", self)
            raise
        finally:
            logger.info("ZeroMQ event monitor stopped: %s", self)

    @staticmethod
    def _process_multipart(
        multipart: tuple[bytes, bytes, bytes],
    ) -> tuple[str, datetime, str]:
        # parse the message according to the format we publish them with
        topic, timestamp, msg = multipart

        # parse timestamp
        timestamp = datetime.fromisoformat(timestamp.decode())

        return topic.decode(), timestamp, msg.decode()

    def recv(self) -> tuple[str, datetime, str]:
        """Receive a single message and decode it."""
        return self._process_multipart(self._subscriber.recv_multipart())

    def close(self):
        """Close I/O resources."""

        self._subscriber.close()
        self._ctx.destroy()

        self.is_connected = False

    @property
    def topics(self):
        """Returns the topics of the subscriber"""
        return self._topics

    def __enter__(self):
        self._thread = Thread(target=self._event_monitor_thread)
        self._thread.start()
        return self

    def __exit__(self, *args):
        with suppress(zmq.ZMQError):
            self._subscriber.disable_monitor()

        self._thread.join()
        self.close()


class AsyncZeroMQSubscriber(ZeroMQSubscriber):
    """Asynchronous version of ZeroMQSubscriber. Use `async_recv` instead of `recv`
    to receive messages. Usage:

    with AsyncZeroMQSubscriber("tcp://host:port", ["topic"]) as subscriber:
        (topic, timestamp, message) = await subscriber.async_recv()
    """

    def __init__(
        self,
        connect_uri: str,
        topics: list[bytes | str],
        event_loop=None,
    ):
        self._event_loop = event_loop or asyncio.get_event_loop()
        self._task = None
        super().__init__(connect_uri, topics)

    @staticmethod
    def _new_zmq_context():
        return zmq.asyncio.Context()

    async def _event_monitor_task(self):
        """Task running the event monitor."""

        logger.info("ZeroMQ event monitor started: %s", self)

        try:
            while await self.monitor.poll():
                evt = await recv_monitor_message(self.monitor)
                if evt["event"] == zmq.EVENT_MONITOR_STOPPED:
                    break

                self._handle_event(evt)
        except (zmq.error.ContextTerminated, CancelledError):
            raise
        except Exception:
            logger.exception("Error in ZeroMQ event monitor: %s", self)
            raise
        finally:
            logger.info("ZeroMQ event monitor stopped: %s", self)

    async def __aenter__(self):
        self._task = self._event_loop.create_task(self._event_monitor_task())
        return self

    def __enter__(self):
        raise NotImplementedError("Use async wait instead")

    async def __aexit__(self, *args):
        # disable monitor
        logger.debug("ZeroMQ teardown stopping monitor: %s", self)
        with suppress(zmq.ZMQError):
            self._subscriber.disable_monitor()

        # cancel task, do not wait for graceful exit
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            _ = await self._task

        # close sockets & context
        logger.debug("ZeroMQ teardown closing socket: %s", self)
        self.close()
        logger.info("ZeroMQ teardown finished: %s", self)

    async def async_recv(self) -> tuple[str, datetime, str]:
        """Receive a single message and decode it."""

        return self._process_multipart(await self._subscriber.recv_multipart())

    def recv(self):
        raise NotImplementedError("Use async_recv() instead")
