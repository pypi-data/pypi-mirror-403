"""Hiring API domain."""

from pybob_sdk.hiring.api import HiringAPI
from pybob_sdk.hiring.models import JobAd, JobAdSearchRequest

__all__ = [
    "HiringAPI",
    "JobAd",
    "JobAdSearchRequest",
]
