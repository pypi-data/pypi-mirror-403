# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Baseline calculation functions.

Baselines are ordered like
    0-0, 1-0, 1-1, 2-0, 2-1, 2-2, ...

if

    b = baseline
    x = stat1 (major)
    y = stat2 (minor)
    x >= y

then

    b_xy = x * (x + 1) / 2 + y

let

    u := b_x0

then

    u            = x * (x + 1) / 2
    8u           = 4x^2 + 4x
    8u + 1       = 4x^2 + 4x + 1 = (2x + 1)^2
    sqrt(8u + 1) = 2x + 1
    x            = (sqrt(8u + 1) - 1) / 2

Let us define

    x'(b) = (sqrt(8b + 1) - 1) / 2

which increases monotonically and is a continuation of y(b).

Because y simply increases by 1 when b increases enough, we
can just take the floor function to obtain the discrete y(b):

   x(b) = floor(x'(b))

        = floor(sqrt(8b + 1) - 1) / 2)

"""

import math


def nr_baselines(nr_inputs: int) -> int:
    """Return the number of baselines (unique pairs) that exist between inputs."""
    return nr_inputs * (nr_inputs + 1) // 2


def baseline_index(major: int, minor: int) -> int:
    """give the unique array index for the baseline (major,minor)

    :raise ValueError: if major < minor.
    """

    if major < minor:
        raise ValueError(
            f"major < minor: {major} < {minor}. Since we do not store the conjugates"
            f"this will lead to processing errors."
        )

    return major * (major + 1) // 2 + minor


def baseline_from_index(index: int) -> tuple:
    """Return the (major,minor) input pair given a baseline index."""

    major = int((math.sqrt(float(8 * index + 1)) - 0.99999) / 2)
    minor = index - baseline_index(major, 0)

    return major, minor
