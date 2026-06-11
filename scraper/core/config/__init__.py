"""
scraper.core.config — single source of truth for runtime configuration.

Sprint 16 Wave 1 (v2 design, 2026-06-11):
- Config class lives in settings.py
- Config.ITEM_IDS was DELETED (dual-voice P0-5: overengineering for 15 items).
  Use Config.load_items() instead.
- yaml items loaded on demand; no eager class-level list.
"""
