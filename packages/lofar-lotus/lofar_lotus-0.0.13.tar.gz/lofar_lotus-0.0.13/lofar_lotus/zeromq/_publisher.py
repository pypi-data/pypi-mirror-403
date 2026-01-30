#  Copyright (C) 2026 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""Base class for ZMQ publishers"""

import logging
import queue
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable, Optional

import zmq
from zmq import Socket

logger = logging.getLogger()

__all__ = ["ZeroMQPublisher"]


class ZeroMQPublisher:  # pylint: disable=too-many-instance-attributes
    """Base class for ZMQ publishers"""

    def __init__(
        self,
        bind_uri: str,
        topics: list[bytes | str],
        queue_size: int = 100,
    ):
        """
        param bind_uri: uri to bind of pattern protocol://ip:port
        param topics: List of topics to publish to, for bytearray use str.encode()
        """
        # define variables early in case __del__ gets called after an
        # exception in __init__
        self._thread = None

        self._queue = queue.Queue(maxsize=queue_size)
        self._ctx = zmq.Context.instance()
        self._publisher = self._ctx.socket(zmq.PUB)

        if isinstance(topics, list) and all(isinstance(y, str) for y in topics):
            self._topics = [topic.encode() for topic in topics]
        else:
            self._topics = topics

        self._publisher.bind(bind_uri)
        self._is_running = False
        self._is_stopping = False
        self._thread = ThreadPoolExecutor(max_workers=1)
        self._future = self._thread.submit(self._run)

    def __del__(self):
        self.shutdown()

    @staticmethod
    def construct_bind_uri(protocol: str, bind: str, port: str | int) -> str:
        """Combine parameters into a full bind uri for ZeroMQ"""
        if isinstance(port, int):
            port = str(port)
        return f"{protocol}://{bind}:{port}"

    @property
    def is_stopping(self):
        """If the request has been made to stop the publisher

        Remains true even after fully stopping
        """
        return self._is_stopping

    @property
    def is_running(self):
        """If the publisher has started"""
        # don't use self._future.is_running, returns false if thread sleeps ;)
        return self._is_running and not self.is_done

    @property
    def is_done(self) -> bool:
        """If the publisher has fully stopped"""
        return self._future.done()

    @property
    def topics(self) -> list[bytes]:
        """Returns the topics ZMQ is publishing to"""
        return self._topics

    @property
    def publisher(self) -> Socket:
        """Returns ZMQ publisher socket"""
        return self._publisher

    def get_result(self, timeout=None) -> object:
        """Return the returned result of the publisher.

        If the publisher threw an exception, it will be raised here."""

        return self._future.result(timeout=timeout)

    def get_exception(self, timeout=None) -> Optional[Exception]:
        """Return the exception the exeption raised by the publisher, or None."""

        return self._future.exception(timeout=timeout)

    def register_callback(self, fn: Callable[[Future], None]):
        """Register a callback to run when the publisher finishes."""

        self._future.add_done_callback(fn)

    @property
    def queue_fill(self) -> int:
        """Return the number of items in the queue."""

        return self._queue.qsize()

    @property
    def queue_size(self) -> int:
        """Return the maximum number of items that fit in the queue."""

        return self._queue.maxsize

    def _run(self):
        """Run the publishing thread."""

        self._is_running = True
        logger.info("Publisher thread: %s starting", self)
        while not self._is_stopping:
            try:
                topics, message = self._queue.get(timeout=1)
                try:
                    now = datetime.now().astimezone(tz=timezone.utc).isoformat()
                    for topic in topics:
                        logger.debug(
                            "Publisher send message with payload of size: %s",
                            len(message),
                        )
                        msg = [topic, now.encode("utf-8"), f"{message}".encode("utf-8")]
                        self._publisher.send_multipart(msg)
                finally:
                    self._queue.task_done()
            except queue.Empty:
                logger.debug("Queue is empty, nothing to publish")
                continue
            except zmq.ZMQError as e:
                if e.errno != zmq.ETERM:
                    self._stop()
                    raise e
            except KeyboardInterrupt as e:
                self._stop()
                raise e
        self._stop()

    def _stop(self):
        """Internal function to handle stopping"""
        self._publisher.close()
        logger.info("Terminated thread of %s", self)
        self._is_running = False

    def shutdown(self):
        """External function to request stopping / shutdown"""
        logger.debug("Request to stop thread of %s", self)
        self._is_stopping = True

        if self._thread:
            self._thread.shutdown()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def send(self, msg, topic: str | bytes | list[bytes | str] = None):
        """
        param msg: The message to enqueue for transmission
        raises queue.Full: If the message could not be enqueued
        """
        if topic is None:
            topic = self._topics
        if not isinstance(topic, list):
            topic = [topic]
        if topic is bytes:
            topic = [topic]
        if isinstance(topic, list) and all(isinstance(y, str) for y in topic):
            topic = [topic.encode() for topic in topic]

        self._queue.put_nowait((topic, msg))
