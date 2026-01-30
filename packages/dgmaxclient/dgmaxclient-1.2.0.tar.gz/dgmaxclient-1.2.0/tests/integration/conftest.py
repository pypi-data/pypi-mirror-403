from __future__ import annotations

import os

import pytest

from dgmaxclient import DGMaxClient


@pytest.fixture()
def client() -> DGMaxClient:
    return DGMaxClient(
        api_key=os.environ.get("DGMAX_API_KEY"),
        base_url=os.environ.get("DGMAX_BASE_URL"),
    )


@pytest.fixture()
def company_id() -> str:
    return os.environ.get("DGMAX_COMPANY_ID")
