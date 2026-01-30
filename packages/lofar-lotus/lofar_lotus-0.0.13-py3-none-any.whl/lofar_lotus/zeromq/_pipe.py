# Copyright (C) 2024 ASTRON (Netherlands Institute for Radio Astronomy)
# SPDX-License-Identifier: Apache-2.0

"""Construct a ZMQ socket pair forming a pipe."""

import binascii
import os
from typing import Tuple

import zmq


def zpipe(ctx) -> Tuple[zmq.Socket, zmq.Socket]:
    """build inproc pipe for talking to threads

    mimic pipe used in czmq zthread_fork.

    Returns a pair of PAIRs connected via inproc
    """
    a = ctx.socket(zmq.PAIR)
    b = ctx.socket(zmq.PAIR)
    a.linger = b.linger = 0
    a.hwm = b.hwm = 1
    iface = f"inproc://{binascii.hexlify(os.urandom(8))}"
    a.bind(iface)
    b.connect(iface)
    return a, b
