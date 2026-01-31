"""
Unit tests for configuration management.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path

from virtualizor_forwarding.config import ConfigManager, ConfigError
from virtualizor_forwarding.models import HostProfile, Config


class TestConfigManager:
    """Tests for ConfigManager class."""

    @pytest.fixture
    def temp_config_path(self):
        """Create temporary config file path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def config_manager(self, temp_config_path):
        """Create ConfigManager with temp path."""
        return ConfigManager(config_path=temp_config_path)

    def test_init_default_path(self):
        """Test initialization with default path."""
        manager = ConfigManager()
        assert "virtualizor-forwarding" in str(manager.config_path)
        assert manager.config_path.name == "config.json"

    def test_init_custom_path(self, temp_config_path):
        """Test initialization with custom path."""
        manager = ConfigManager(config_path=temp_config_path)
        assert str(manager.config_path) == temp_config_path

    def test_load_nonexistent_file(self, config_manager):
        """Test loading when config file doesn't exist."""
        # Remove the temp file if it exists
        if config_manager.config_path.exists():
            os.unlink(config_manager.config_path)

        config = config_manager.load()
        assert isinstance(config, Config)
        assert config.hosts == {}
        assert config.default_host is None

    def test_load_valid_config(self, config_manager):
        """Test loading valid config file."""
        # Write valid config
        config_data = {
            "hosts": {
                "prod": {
                    "name": "prod",
                    "api_url": "https://example.com:4083/index.php",
                    "api_key": "key",
                    "api_pass": "pass",
                }
            },
            "default_host": "prod",
            "version": "1.0",
        }
        with open(config_manager.config_path, "w") as f:
            json.dump(config_data, f)

        config = config_manager.load()
        assert "prod" in config.hosts
        assert config.default_host == "prod"

    def test_load_corrupted_config(self, config_manager):
        """Test loading corrupted config file."""
        with open(config_manager.config_path, "w") as f:
            f.write("not valid json {{{")

        with pytest.raises(ConfigError) as exc_info:
            config_manager.load()
        assert "corrupted" in str(exc_info.value).lower()

    def test_save_config(self, config_manager):
        """Test saving config."""
        profile = HostProfile(
            name="test",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="pass",
        )
        config = Config(hosts={"test": profile}, default_host="test")
        config_manager.save(config)

        # Verify file was written
        assert config_manager.config_path.exists()
        with open(config_manager.config_path) as f:
            data = json.load(f)
        assert "test" in data["hosts"]

    def test_add_host(self, config_manager):
        """Test adding a host."""
        profile = HostProfile.create(
            name="prod",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="password",
        )
        config_manager.add_host("prod", profile)

        config = config_manager.load()
        assert "prod" in config.hosts
        # First host should be set as default
        assert config.default_host == "prod"

    def test_add_host_duplicate(self, config_manager):
        """Test adding duplicate host raises error."""
        profile = HostProfile.create(
            name="prod",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="password",
        )
        config_manager.add_host("prod", profile)

        with pytest.raises(ConfigError) as exc_info:
            config_manager.add_host("prod", profile)
        assert "already exists" in str(exc_info.value)

    def test_remove_host(self, config_manager):
        """Test removing a host."""
        profile = HostProfile.create(
            name="prod",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="password",
        )
        config_manager.add_host("prod", profile)
        config_manager.remove_host("prod")

        config = config_manager.load()
        assert "prod" not in config.hosts

    def test_remove_nonexistent_host(self, config_manager):
        """Test removing nonexistent host raises error."""
        config_manager.load()  # Initialize empty config
        with pytest.raises(ConfigError) as exc_info:
            config_manager.remove_host("nonexistent")
        assert "does not exist" in str(exc_info.value)

    def test_remove_default_host_updates_default(self, config_manager):
        """Test removing default host updates default to another host."""
        profile1 = HostProfile.create(
            name="prod",
            api_url="https://prod.com:4083/index.php",
            api_key="key1",
            api_pass="pass1",
        )
        profile2 = HostProfile.create(
            name="staging",
            api_url="https://staging.com:4083/index.php",
            api_key="key2",
            api_pass="pass2",
        )
        config_manager.add_host("prod", profile1)
        config_manager.add_host("staging", profile2)
        config_manager.set_default("prod")

        config_manager.remove_host("prod")
        config = config_manager.load()
        assert config.default_host == "staging"

    def test_get_host(self, config_manager):
        """Test getting a specific host."""
        profile = HostProfile.create(
            name="prod",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="password",
        )
        config_manager.add_host("prod", profile)

        retrieved = config_manager.get_host("prod")
        assert retrieved.name == "prod"
        assert retrieved.api_url == "https://example.com:4083/index.php"

    def test_get_nonexistent_host(self, config_manager):
        """Test getting nonexistent host raises error."""
        config_manager.load()
        with pytest.raises(ConfigError) as exc_info:
            config_manager.get_host("nonexistent")
        assert "does not exist" in str(exc_info.value)

    def test_list_hosts(self, config_manager):
        """Test listing all hosts."""
        profile1 = HostProfile.create(
            name="prod",
            api_url="https://prod.com:4083/index.php",
            api_key="key1",
            api_pass="pass1",
        )
        profile2 = HostProfile.create(
            name="staging",
            api_url="https://staging.com:4083/index.php",
            api_key="key2",
            api_pass="pass2",
        )
        config_manager.add_host("prod", profile1)
        config_manager.add_host("staging", profile2)

        hosts = config_manager.list_hosts()
        assert "prod" in hosts
        assert "staging" in hosts
        assert len(hosts) == 2

    def test_set_default(self, config_manager):
        """Test setting default host."""
        profile1 = HostProfile.create(
            name="prod",
            api_url="https://prod.com:4083/index.php",
            api_key="key1",
            api_pass="pass1",
        )
        profile2 = HostProfile.create(
            name="staging",
            api_url="https://staging.com:4083/index.php",
            api_key="key2",
            api_pass="pass2",
        )
        config_manager.add_host("prod", profile1)
        config_manager.add_host("staging", profile2)

        config_manager.set_default("staging")
        assert config_manager.get_default_name() == "staging"

    def test_set_default_nonexistent(self, config_manager):
        """Test setting nonexistent host as default raises error."""
        config_manager.load()
        with pytest.raises(ConfigError):
            config_manager.set_default("nonexistent")

    def test_get_default(self, config_manager):
        """Test getting default host profile."""
        profile = HostProfile.create(
            name="prod",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="password",
        )
        config_manager.add_host("prod", profile)

        default = config_manager.get_default()
        assert default is not None
        assert default.name == "prod"

    def test_get_default_none(self, config_manager):
        """Test getting default when none set."""
        config_manager.load()
        default = config_manager.get_default()
        assert default is None

    def test_has_hosts_true(self, config_manager):
        """Test has_hosts returns True when hosts exist."""
        profile = HostProfile.create(
            name="prod",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="password",
        )
        config_manager.add_host("prod", profile)
        assert config_manager.has_hosts() is True

    def test_has_hosts_false(self, config_manager):
        """Test has_hosts returns False when no hosts."""
        config_manager.load()
        assert config_manager.has_hosts() is False

    def test_get_all_hosts(self, config_manager):
        """Test getting all hosts."""
        profile1 = HostProfile.create(
            name="prod",
            api_url="https://prod.com:4083/index.php",
            api_key="key1",
            api_pass="pass1",
        )
        profile2 = HostProfile.create(
            name="staging",
            api_url="https://staging.com:4083/index.php",
            api_key="key2",
            api_pass="pass2",
        )
        config_manager.add_host("prod", profile1)
        config_manager.add_host("staging", profile2)

        all_hosts = config_manager.get_all_hosts()
        assert len(all_hosts) == 2
        assert "prod" in all_hosts
        assert "staging" in all_hosts
