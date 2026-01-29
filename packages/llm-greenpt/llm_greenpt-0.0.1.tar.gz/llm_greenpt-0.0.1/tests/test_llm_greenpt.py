"""Tests for llm-greenpt plugin."""
import pytest
import llm
from llm.plugins import load_plugins, pm


def test_plugin_is_installed():
    """Test that the plugin is properly installed and loaded."""
    load_plugins()
    names = [mod.__name__ for mod in pm.get_plugins()]
    assert "llm_greenpt" in names


def test_plugin_registered():
    """Test that the plugin models are registered."""
    models = llm.get_models_with_aliases()
    model_ids = [m.model.model_id for m in models]
    
    # Check that at least the main GreenPT models are registered
    assert "greenpt/green-l" in model_ids
    assert "greenpt/green-l-raw" in model_ids
    assert "greenpt/green-r" in model_ids
    assert "greenpt/green-r-raw" in model_ids


def test_model_str():
    """Test model string representation."""
    model = llm.get_model("greenpt/green-l")
    assert str(model) == "GreenPT: greenpt/green-l"


def test_model_aliases():
    """Test that aliases work."""
    # These should all resolve to models
    model1 = llm.get_model("greenpt-large")
    model2 = llm.get_model("greenpt-reasoning")
    
    assert model1.model_id == "greenpt/green-l"
    assert model2.model_id == "greenpt/green-r"


def test_needs_key():
    """Test that models require the greenpt key."""
    model = llm.get_model("greenpt/green-l")
    assert model.needs_key == "greenpt"
    assert model.key_env_var == "GREENPT_API_KEY"
