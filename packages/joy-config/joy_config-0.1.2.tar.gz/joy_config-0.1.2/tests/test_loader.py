from joy_config.loader import auto_loader


def test_auto_loader():
    # Test that the auto_loader function can load a module
    module = auto_loader()
    assert module is not None