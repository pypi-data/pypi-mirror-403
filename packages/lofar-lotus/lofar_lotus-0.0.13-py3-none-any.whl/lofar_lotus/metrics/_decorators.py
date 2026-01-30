# Copyright (C) 2025 ASTRON (Netherlands Institute for Radio Astronomy)
# SPDX-License-Identifier: Apache-2.0

from functools import wraps

from prometheus_client import Counter

from ._metrics import Metric


def call_exception_metrics(
    service_name: str,
    static_labels: dict[str, str] | None = None,
):
    """Decorator that: maintains call and exception counts as
    Prometheus metrics."""

    def wrapper(func):
        labels = {"service": service_name}
        labels.update(static_labels or {})

        call_count_metric = Metric(
            f"{func.__name__}_calls",
            f"Call statistics for {func.__qualname__}",
            labels,
            metric_class=Counter,
        )
        exception_count_metric = Metric(
            f"{func.__name__}_exceptions",
            f"Number of exceptions thrown by {func.__qualname__}",
            labels,
            metric_class=Counter,
        )

        # make sure the metrics exist even if the function
        # is never called
        call_count_metric.get_metric().inc(0)
        exception_count_metric.get_metric().inc(0)

        @wraps(func)
        def inner(*args, **kwargs):
            try:
                call_count_metric.get_metric().inc()

                return func(*args, **kwargs)
            except Exception:
                exception_count_metric.get_metric().inc()
                raise

        return inner

    return wrapper
