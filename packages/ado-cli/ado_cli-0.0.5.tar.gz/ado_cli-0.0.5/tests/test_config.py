import tempfile
from pathlib import Path


def test_config():
    """Test configuration management"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.json"

        # Mock the config file location
        import ado.config as config_module

        original_file = config_module.CONFIG_FILE
        config_module.CONFIG_FILE = str(config_file)

        try:
            from ado.config import AdoConfig

            # Test config operations
            cfg = AdoConfig()
            assert cfg.get("nonexistent") is None
            assert cfg.get("nonexistent", "default") == "default"

            cfg.set("test_key", "test_value")
            assert cfg.get("test_key") == "test_value"
            assert config_file.exists()

            # Test persistence
            cfg2 = AdoConfig()
            assert cfg2.get("test_key") == "test_value"

            # Test removal
            cfg.remove("test_key")
            assert cfg.get("test_key") is None

            print("✓ All config tests passed")
        finally:
            config_module.CONFIG_FILE = original_file


if __name__ == "__main__":
    test_config()
