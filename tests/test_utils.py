"""Tests for the utils module."""

import unittest
from unittest.mock import patch

from iranleague_exporter.utils import get_env


class TestGetEnvFunction(unittest.TestCase):
    @patch.dict("os.environ", {"TEST_KEY": "test_value"}, clear=True)
    def test_env_variable_set(self):
        """Test when the environment variable is set."""
        result = get_env("TEST_KEY")
        self.assertEqual(result, "test_value")

    @patch.dict("os.environ", {}, clear=True)
    def test_env_variable_not_set_with_default(self):
        """Test when the environment variable is not set but a default is provided."""
        result = get_env("TEST_KEY", default="default_value")
        self.assertEqual(result, "default_value")

    @patch.dict("os.environ", {}, clear=True)
    def test_env_variable_not_set_without_default(self):
        """Test when the environment variable is not set and no default is provided."""
        with self.assertRaises(OSError) as context:
            get_env("TEST_KEY")
        self.assertIn(
            "Environment variable 'TEST_KEY' is not set.", str(context.exception)
        )

    @patch.dict("os.environ", {"TEST_KEY": "test_value"}, clear=True)
    def test_get_env_with_default_key_present(self):
        """Test when the environment variable is set even when a default is provided."""
        result = get_env("TEST_KEY", default="default_value")
        self.assertEqual(result, "test_value")

    @patch.dict("os.environ", {}, clear=True)
    def test_get_env_default_is_none(self):
        """Test get_env returns None when key is absent and default is None."""
        with self.assertRaises(Exception) as context:
            get_env("MISSING_KEY", default=None)
        self.assertIn(
            "Environment variable 'MISSING_KEY' is not set.", str(context.exception)
        )

    @patch.dict("os.environ", {"TEST_KEY": ""}, clear=True)
    def test_env_variable_set_to_empty(self):
        """Test when the environment variable is explicitly set to an empty string."""
        with self.assertRaises(OSError) as context:
            get_env("TEST_KEY")
        self.assertIn(
            "Environment variable 'TEST_KEY' is not set.", str(context.exception)
        )
