# conftest.py
"""Test configuration to enable async test support.
"""
import pytest

# Explicitly load pytest-asyncio plugin
pytest_plugins = ["pytest_asyncio"]
