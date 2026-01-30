#  Copyright (C) 2025 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

from prometheus_client import disable_created_metrics, start_http_server
from prometheus_client.registry import REGISTRY

from ._decorators import call_exception_metrics
from ._metrics import METRICS, Metric

__all__ = [
    "start_metrics_server",
    "Metric",
    "call_exception_metrics",
    "clear_metric_registry",
]


def start_metrics_server(port: int = 8000):
    """Start the metrics servers, defaults to port 8000"""
    # configure
    disable_created_metrics()

    # start server
    start_http_server(port)


def clear_metric_registry():
    """Clear all metrics to make sure we don't register the same one twice
    between tests (the library forbids it)."""

    # Metrics draw copies of prometheus_client.registry.REGISTRY,
    # and that does not provide a public interface to query the registered collectors.
    for collector in list(REGISTRY._collector_to_names.keys()):
        REGISTRY.unregister(collector)

    # Clear Lotus' internal registry as well
    METRICS.clear()
