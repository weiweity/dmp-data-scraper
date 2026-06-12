"""Tests for T_OFFSET / get_target_date utilities."""
from datetime import date, timedelta

import pytest

from core.utils.t_offset import get_target_date


def test_get_target_date_default_is_yesterday(monkeypatch) -> None:
    """With no env and no arg, get_target_date() returns today - 1 day."""
    monkeypatch.delenv("T_OFFSET", raising=False)
    result = get_target_date()
    assert result == date.today() - timedelta(days=1)


def test_get_target_date_offset_2_returns_2_days_ago(monkeypatch) -> None:
    """get_target_date(t_offset=2) returns today - 2 days."""
    monkeypatch.delenv("T_OFFSET", raising=False)
    result = get_target_date(t_offset=2)
    assert result == date.today() - timedelta(days=2)


def test_get_target_date_offset_0_returns_today(monkeypatch) -> None:
    """get_target_date(t_offset=0) returns today."""
    monkeypatch.delenv("T_OFFSET", raising=False)
    result = get_target_date(t_offset=0)
    assert result == date.today()


def test_t_offset_env_var_3_returns_3_days_ago(monkeypatch) -> None:
    """When T_OFFSET=3 env var is set, get_target_date() returns today - 3 days."""
    monkeypatch.setenv("T_OFFSET", "3")
    result = get_target_date()
    assert result == date.today() - timedelta(days=3)
