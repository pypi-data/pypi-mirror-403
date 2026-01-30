"""Basic tests for discord-mcp-agent."""

import pytest


def test_import():
    """Test that the package can be imported."""
    import discord_mcp_agent
    assert hasattr(discord_mcp_agent, "__version__")


def test_version():
    """Test version string format."""
    from discord_mcp_agent import __version__
    assert isinstance(__version__, str)
    assert len(__version__.split(".")) >= 2


def test_exports():
    """Test that main exports are available."""
    from discord_mcp_agent import main, main_sync
    assert callable(main)
    assert callable(main_sync)
