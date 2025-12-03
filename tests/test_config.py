"""Tests for the config module."""

import os
import unittest
from unittest.mock import patch

from iranleague_exporter.config import (
    AppConfig,
    AuthConfig,
    CrawlerConfig,
    HTTPConfig,
    Language,
    LogLevel,
    _get_float_env,
    _get_int_env,
    _get_language_env,
    _get_log_level_env,
    get_config,
    reset_config,
)


class TestLogLevel(unittest.TestCase):
    """Tests for LogLevel enum."""

    def test_log_levels(self):
        """Test all log levels exist."""
        self.assertEqual(LogLevel.DEBUG.value, "DEBUG")
        self.assertEqual(LogLevel.INFO.value, "INFO")
        self.assertEqual(LogLevel.WARNING.value, "WARNING")
        self.assertEqual(LogLevel.ERROR.value, "ERROR")
        self.assertEqual(LogLevel.CRITICAL.value, "CRITICAL")


class TestLanguage(unittest.TestCase):
    """Tests for Language enum."""

    def test_languages(self):
        """Test all languages exist."""
        self.assertEqual(Language.FA.value, "FA")
        self.assertEqual(Language.EN.value, "EN")


class TestHTTPConfig(unittest.TestCase):
    """Tests for HTTPConfig dataclass."""

    def test_default_values(self):
        """Test default HTTPConfig values."""
        config = HTTPConfig()
        self.assertEqual(config.host, "0.0.0.0")
        self.assertEqual(config.port, 8000)
        self.assertEqual(config.workers, 1)


class TestCrawlerConfig(unittest.TestCase):
    """Tests for CrawlerConfig dataclass."""

    def test_default_values(self):
        """Test default CrawlerConfig values."""
        config = CrawlerConfig()
        self.assertEqual(config.url, "https://iranleague.ir/fa/MatchSchedule/1/1")
        self.assertEqual(config.connect_timeout, 5.0)
        self.assertEqual(config.read_timeout, 10.0)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.retry_backoff_factor, 0.5)
        self.assertEqual(config.user_agent, "IranLeagueExporter/1.0")


class TestAuthConfig(unittest.TestCase):
    """Tests for AuthConfig dataclass."""

    def test_is_configured_false(self):
        """Test is_configured returns False when not configured."""
        config = AuthConfig()
        self.assertFalse(config.is_configured())

    def test_is_configured_true(self):
        """Test is_configured returns True when configured."""
        config = AuthConfig(username="user", password="pass")
        self.assertTrue(config.is_configured())

    def test_is_configured_partial(self):
        """Test is_configured returns False with partial config."""
        config = AuthConfig(username="user", password="")
        self.assertFalse(config.is_configured())


class TestAppConfig(unittest.TestCase):
    """Tests for AppConfig dataclass."""

    def setUp(self):
        """Reset config before each test."""
        reset_config()

    def tearDown(self):
        """Reset config after each test."""
        reset_config()

    @patch.dict(
        os.environ,
        {
            "AUTH_USERNAME": "testuser",
            "AUTH_PASSWORD": "testpass",
        },
        clear=True,
    )
    def test_from_env_basic(self):
        """Test loading config from environment."""
        config = AppConfig.from_env()
        self.assertEqual(config.auth.username, "testuser")
        self.assertEqual(config.auth.password, "testpass")

    @patch.dict(
        os.environ,
        {
            "AUTH_USERNAME": "testuser",
            "AUTH_PASSWORD": "testpass",
            "HTTP_PORT": "9000",
            "UPDATE_INTERVAL": "60",
            "LOG_LEVEL": "DEBUG",
        },
        clear=True,
    )
    def test_from_env_custom_values(self):
        """Test loading custom config from environment."""
        config = AppConfig.from_env()
        self.assertEqual(config.http.port, 9000)
        self.assertEqual(config.update_interval_minutes, 60)
        self.assertEqual(config.log_level, LogLevel.DEBUG)

    def test_update_interval_seconds(self):
        """Test update_interval_seconds property."""
        config = AppConfig(update_interval_minutes=30)
        self.assertEqual(config.update_interval_seconds, 1800)

    @patch.dict(
        os.environ,
        {
            "AUTH_USERNAME": "testuser",
            "AUTH_PASSWORD": "testpass",
        },
        clear=True,
    )
    def test_validate_success(self):
        """Test validation with valid config."""
        config = AppConfig.from_env()
        errors = config.validate()
        self.assertEqual(errors, [])

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_missing_auth(self):
        """Test validation fails without auth."""
        config = AppConfig.from_env()
        errors = config.validate()
        self.assertTrue(any("Authentication" in e for e in errors))

    def test_validate_invalid_interval(self):
        """Test validation fails with invalid interval."""
        config = AppConfig(
            auth=AuthConfig(username="u", password="p"),
            update_interval_minutes=0,
        )
        errors = config.validate()
        self.assertTrue(any("UPDATE_INTERVAL" in e for e in errors))

    def test_validate_invalid_port(self):
        """Test validation fails with invalid port."""
        config = AppConfig(
            auth=AuthConfig(username="u", password="p"),
            http=HTTPConfig(port=99999),
        )
        errors = config.validate()
        self.assertTrue(any("HTTP_PORT" in e for e in errors))


class TestEnvHelpers(unittest.TestCase):
    """Tests for environment helper functions."""

    @patch.dict(os.environ, {"TEST_INT": "42"}, clear=True)
    def test_get_int_env(self):
        """Test _get_int_env with valid value."""
        result = _get_int_env("TEST_INT", 0)
        self.assertEqual(result, 42)

    @patch.dict(os.environ, {}, clear=True)
    def test_get_int_env_default(self):
        """Test _get_int_env returns default."""
        result = _get_int_env("MISSING", 10)
        self.assertEqual(result, 10)

    @patch.dict(os.environ, {"TEST_INT": "not_an_int"}, clear=True)
    def test_get_int_env_invalid(self):
        """Test _get_int_env raises on invalid value."""
        with self.assertRaises(ValueError):
            _get_int_env("TEST_INT", 0)

    @patch.dict(os.environ, {"TEST_FLOAT": "3.14"}, clear=True)
    def test_get_float_env(self):
        """Test _get_float_env with valid value."""
        result = _get_float_env("TEST_FLOAT", 0.0)
        self.assertAlmostEqual(result, 3.14)

    @patch.dict(os.environ, {}, clear=True)
    def test_get_float_env_default(self):
        """Test _get_float_env returns default."""
        result = _get_float_env("MISSING", 1.5)
        self.assertAlmostEqual(result, 1.5)

    @patch.dict(os.environ, {"TEST_LEVEL": "DEBUG"}, clear=True)
    def test_get_log_level_env(self):
        """Test _get_log_level_env with valid value."""
        result = _get_log_level_env("TEST_LEVEL", LogLevel.INFO)
        self.assertEqual(result, LogLevel.DEBUG)

    @patch.dict(os.environ, {"TEST_LEVEL": "debug"}, clear=True)
    def test_get_log_level_env_lowercase(self):
        """Test _get_log_level_env handles lowercase."""
        result = _get_log_level_env("TEST_LEVEL", LogLevel.INFO)
        self.assertEqual(result, LogLevel.DEBUG)

    @patch.dict(os.environ, {"TEST_LEVEL": "INVALID"}, clear=True)
    def test_get_log_level_env_invalid(self):
        """Test _get_log_level_env raises on invalid value."""
        with self.assertRaises(ValueError):
            _get_log_level_env("TEST_LEVEL", LogLevel.INFO)

    @patch.dict(os.environ, {"TEST_LANG": "FA"}, clear=True)
    def test_get_language_env(self):
        """Test _get_language_env with valid value."""
        result = _get_language_env("TEST_LANG", Language.EN)
        self.assertEqual(result, Language.FA)

    @patch.dict(os.environ, {"TEST_LANG": "INVALID"}, clear=True)
    def test_get_language_env_invalid(self):
        """Test _get_language_env raises on invalid value."""
        with self.assertRaises(ValueError):
            _get_language_env("TEST_LANG", Language.EN)


class TestConfigSingleton(unittest.TestCase):
    """Tests for config singleton behavior."""

    def setUp(self):
        """Reset config before each test."""
        reset_config()

    def tearDown(self):
        """Reset config after each test."""
        reset_config()

    @patch.dict(
        os.environ,
        {
            "AUTH_USERNAME": "test",
            "AUTH_PASSWORD": "test",
        },
        clear=True,
    )
    def test_get_config_returns_same_instance(self):
        """Test get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        self.assertIs(config1, config2)

    @patch.dict(
        os.environ,
        {
            "AUTH_USERNAME": "test",
            "AUTH_PASSWORD": "test",
        },
        clear=True,
    )
    def test_reset_config_clears_singleton(self):
        """Test reset_config clears the singleton."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        self.assertIsNot(config1, config2)
