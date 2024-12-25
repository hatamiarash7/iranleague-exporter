"""Tests for the main module."""

import asyncio
import os
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry

from iranleague_exporter.main import (
    app,
    matches_gauge,
    periodic_update,
    update_metrics,
    verify_credentials,
)


class TestMainModule(unittest.TestCase):
    def setUp(self):
        """Set up the FastAPI test client."""
        self.client = TestClient(app)
        self.registry = CollectorRegistry()
        self.test_username = "test_user"
        self.test_password = "test_pass"
        os.environ.setdefault("AUTH_USERNAME", self.test_username)
        os.environ.setdefault("AUTH_PASSWORD", self.test_password)

    def test_verify_credentials_success(self):
        """Test successful verification of credentials."""
        credentials = MagicMock(
            username=self.test_username,
            password=self.test_password,
        )

        username = verify_credentials(credentials)
        self.assertEqual(username, self.test_username)

    def test_verify_credentials_failure(self):
        """Test failure of credentials verification."""
        credentials = MagicMock(username="wrong_user", password="wrong_pass")

        with self.assertRaises(HTTPException) as context:
            verify_credentials(credentials)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Incorrect username or password", str(context.exception.detail))

    @patch("iranleague_exporter.main.get_matches")
    def test_update_metrics_success(self, mock_get_matches):
        """Test successful update of metrics."""
        mock_get_matches.return_value = [
            {"week": "1", "teams": "TeamA vs TeamB", "timestamp": 1672531200},
            {"week": "2", "teams": "TeamC vs TeamD", "timestamp": 1672617600},
        ]

        update_metrics()

        metric = matches_gauge.labels(teams="TeamA vs TeamB")._value.get()
        self.assertEqual(metric, 1672531200)

        metric = matches_gauge.labels(teams="TeamC vs TeamD")._value.get()
        self.assertEqual(metric, 1672617600)

    @patch("iranleague_exporter.main.get_matches")
    def test_update_metrics_exception(self, mock_get_matches):
        """Test handling exceptions during metric updates."""
        mock_get_matches.side_effect = Exception("Mocked exception")

        with self.assertLogs("uvicorn.error", level="ERROR") as log:
            update_metrics()

        self.assertIn("Error updating metrics: Mocked exception", log.output[0])

    @patch("iranleague_exporter.main.get_matches")
    def test_metrics_endpoint_authenticated(self, mock_get_matches):
        """Test authenticated access to the /metrics endpoint."""
        mock_get_matches.return_value = [
            {"teams": "TeamA vs TeamB", "timestamp": 1672531200},
        ]

        response = self.client.get(
            "/metrics",
            auth=(self.test_username, self.test_password),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("ir_league_matches", response.text)

    def test_metrics_endpoint_unauthorized(self):
        """Test unauthorized access to the /metrics endpoint."""
        response = self.client.get("/metrics", auth=("wrong_user", "wrong_pass"))
        self.assertEqual(response.status_code, 401)
        self.assertIn("Incorrect username or password", response.text)

    @patch("iranleague_exporter.main.update_metrics")
    @patch(
        "asyncio.sleep",
        side_effect=asyncio.CancelledError,
    )  # Simulate task cancellation
    def test_periodic_update(self, mock_sleep, mock_update_metrics):
        """Test periodic update function."""
        with self.assertRaises(asyncio.CancelledError):
            asyncio.run(periodic_update())

        # Ensure update was called at least once
        mock_update_metrics.assert_called_once()
