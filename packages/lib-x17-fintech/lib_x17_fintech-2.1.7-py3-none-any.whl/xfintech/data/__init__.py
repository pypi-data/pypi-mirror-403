"""
Data module for xfintech.

This module provides the core data acquisition and processing infrastructure:

Submodules:
- common: Common utilities (Cache, Retry, Metric, Params, Paginate, Coolant)
- job: Job system with registry and error handling
- relay: Relay client for remote API access
- source: Data source implementations (tushare, baostock)
"""

from . import common, job, relay, source

__all__ = [
    "common",
    "job",
    "relay",
    "source",
]
