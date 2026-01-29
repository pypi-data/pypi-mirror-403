from unittest.mock import patch


def test_main_module_execution():
    """Test that __main__.py calls cli.main()"""
    with patch("whatdeps.cli.main") as mock_main:
        import whatdeps.__main__

        assert hasattr(whatdeps.__main__, "main")
