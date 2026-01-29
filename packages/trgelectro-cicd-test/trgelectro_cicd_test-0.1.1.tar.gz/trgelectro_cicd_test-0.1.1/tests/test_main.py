from src.main import greet


def test_greet_default():
    """Test greeting with default name."""
    assert greet() == "Hello, World!"


def test_greet_custom_name():
    """Test greeting with custom name."""
    assert greet("Alice") == "Hello, Alice!"


def test_greet_empty_string():
    """Test greeting with empty string."""
    assert greet("") == "Hello, !"
