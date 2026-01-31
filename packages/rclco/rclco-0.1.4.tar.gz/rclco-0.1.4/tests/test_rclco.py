from rclco import __version__


def test_version():
    """Test that version is a non-empty string."""
    assert isinstance(__version__, str)
    assert len(__version__) > 0
