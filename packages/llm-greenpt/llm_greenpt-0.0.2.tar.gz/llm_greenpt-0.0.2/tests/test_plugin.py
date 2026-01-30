"""Basic plugin tests for llm-greenpt."""

from llm.plugins import load_plugins, pm


def test_plugin_is_installed():
    """Test that the plugin is properly installed and loaded."""
    load_plugins()
    names = [mod.__name__ for mod in pm.get_plugins()]
    assert "llm_greenpt" in names
