"""Shared pytest fixtures for scraper/core tests."""
import os
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def tmp_csv(tmp_path: Path) -> Path:
    """Factory fixture: returns a callable that writes CSV data to a temp file."""
    def _make(headers: list, rows: list) -> Path:
        p = tmp_path / "data.csv"
        with p.open("w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for r in rows:
                f.write(",".join(str(c) for c in r) + "\n")
        return p
    return _make


@pytest.fixture
def items_yaml_factory(tmp_path: Path):
    """Factory fixture: writes a temporary items.yaml with N items and returns path."""
    def _make(n: int = 3, schema: str = "default") -> Path:
        items = []
        for i in range(n):
            items.append({
                "id": f"item_{i}",
                "name": f"Item {i}",
                "source": f"source_{i}",
                "enabled": True,
            })
        if schema == "invalid":
            items = "this-is-not-a-list"
        payload = {"items": items} if schema != "missing_items" else {"wrong_key": items}
        p = tmp_path / "items.yaml"
        p.write_text(yaml.safe_dump(payload, allow_unicode=True), encoding="utf-8")
        return p
    return _make


@pytest.fixture
def disable_lark_alerts(monkeypatch):
    """Disable Lark alerts by setting LARK_ALERTS_ENABLED=0."""
    monkeypatch.setenv("LARK_ALERTS_ENABLED", "0")
    return monkeypatch


@pytest.fixture
def sample_item_row():
    """Factory for a sample item row dict."""
    def _make(item_id: str = "item_0", date: str = "2026/6/10", gmv: float = 1000.0):
        return {
            "item_id": item_id,
            "date": date,
            "gmv": gmv,
            "orders": 10,
            "uv": 100,
        }
    return _make


@pytest.fixture
def sample_assets_row():
    """Factory for a sample assets row dict."""
    def _make(asset_id: str = "asset_0", date: str = "2026/6/10", spend: float = 500.0):
        return {
            "asset_id": asset_id,
            "date": date,
            "spend": spend,
            "impressions": 10000,
            "clicks": 200,
        }
    return _make


@pytest.fixture
def sample_flow_row():
    """Factory for a sample flow row dict."""
    def _make(flow_id: str = "flow_0", date: str = "2026/6/10", xinzeng: int = 50):
        return {
            "flow_id": flow_id,
            "date": date,
            "xinzeng": xinzeng,
            "active": 1000,
        }
    return _make
