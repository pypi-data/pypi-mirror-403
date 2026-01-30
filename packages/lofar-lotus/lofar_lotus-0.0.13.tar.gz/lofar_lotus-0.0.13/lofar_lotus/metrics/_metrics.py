#  Copyright (C) 2025 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""Metrics"""

import logging
from enum import IntEnum
from typing import Dict, List

from prometheus_client import Enum, Gauge, Info, Metric

__all__ = [
    "Metric",
]

logger = logging.getLogger()

# Global cache to have devices share their metrics for their own attributes,
# as metrics with the same name must exist only once.
METRICS = {}


class Metric:
    """Manage a Prometheus Metric object, allowing more flexibility
    for label management and a generic interface across metric types."""

    # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        name: str,
        description: str,
        static_labels: Dict[str, str],
        metric_class=Gauge,
        metric_class_init_kwargs: Dict[str, object] | None = None,
        dynamic_labels: List[str] | None = None,
    ):
        self.name = name
        self.description = description
        self.metric_class = metric_class

        self.static_label_keys = list(static_labels.keys())
        self.static_label_values = list(static_labels.values())

        self.dynamic_label_keys = dynamic_labels or []

        self.metric_class_init_kwargs = metric_class_init_kwargs or {}

        if self.name not in METRICS:
            METRICS[self.name] = self.make_metric()

        self.metric = METRICS[self.name]
        assert self.metric.__class__ == metric_class, (
            f"Metric {self.name} was previously provided as {self.metric.__class__}"
            f"but is now needed as {metric_class}"
        )

    def __str__(self):
        return (
            f"{self.__class__.__name__}(name={self.name},"
            f"metric_class={self.metric_class}, static_labels={self.static_label_keys},"
            f"dynamic_labels={self.dynamic_label_keys}"
        )

    def clear(self):
        """Remove all cached metrics."""

        self.metric.clear()

    def label_keys(self) -> List[str]:
        """Return the list of labels that we will use."""

        return self.static_label_keys + self.dynamic_label_keys

    def make_metric(self) -> Metric:
        """Construct a metric that collects samples for this attribute."""
        return self.metric_class(
            self.name,
            self.description,
            labelnames=self.label_keys(),
            **self.metric_class_init_kwargs,
        )

    def get_metric(self, dynamic_label_values: List = None) -> Metric:
        """Return the metric that uses the default labels."""
        return self.metric.labels(
            *self.static_label_values, *(dynamic_label_values or [])
        )

    def set_value(self, value: object):
        """A new value for the attribute is known. Feed it to the metric."""

        # set it, this class will take care of the default labels
        self._set_value(value, self.static_label_values)

    def _set_value(self, value: object, labels: List[str]):
        if self.metric_class == Enum:
            self._metric_enum_value(value, labels)
        elif self.metric_class == Info:
            self._metric_info_value(value, labels)
        else:
            self._metric_set_value(value, labels)

    def _metric_set_value(self, value: object, labels: List[str]):
        if value is None:
            raise ValueError(f"Invalid value for metric: {value}")

        metric = self.metric.labels(*labels) if labels else self.metric
        metric.set(value)

    def _metric_info_value(self, value: Dict[str, str], labels: List[str]):
        if value is None or None in value.values():
            raise ValueError(f"Invalid value for metric: {value}")

        metric = self.metric.labels(*labels) if labels else self.metric
        metric.info(value)

    def _metric_enum_value(self, value: str | IntEnum, labels: List[str]):
        if value is None:
            raise ValueError(f"Invalid value for metric: {value}")

        metric = self.metric.labels(*labels) if labels else self.metric
        metric.state(value.name if isinstance(value, (IntEnum)) else value)

    def collect(self) -> List[Metric]:
        """Return all collected samples."""
        return self.metric.collect()
