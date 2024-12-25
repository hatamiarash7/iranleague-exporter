"""Tests for the crawler module."""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

import jdatetime

from iranleague_exporter.crawler import get_matches


class TestGetMatches(unittest.TestCase):
    @patch("iranleague_exporter.crawler.requests.get")
    def test_successful_response_with_valid_data(self, mock_get):
        """Test a successful response with valid HTML content."""
        # Mock HTML response
        mock_html = """
        <html>
            <body>
                <div class="row">
                    <div>Week 1</div>
                    <div>
                        <table>
                            <tbody>
                                <tr>
                                    <td>Team A</td>
                                    <td>-</td>
                                    <td>Team B</td>
                                    <td>1402/10/10</td>
                                    <td>15:30</td>
                                    <td></td>
                                    <td></td>
                                </tr>
                                <tr>
                                    <td>Team C</td>
                                    <td>1 - 0</td>
                                    <td>Team D</td>
                                    <td>1402/10/12</td>
                                    <td>18:00</td>
                                    <td></td>
                                    <td></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response

        date = jdatetime.date(day=10, month=10, year=1402).togregorian()
        time = "15:30"

        result = get_matches()
        expected_result = [
            {
                "teams": "Team-A vs Team-B",
                "timestamp": int(
                    datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").timestamp()
                ),  # Corresponds to 1402/10/10 15:30
            }
        ]

        self.assertEqual(result, expected_result)

    @patch("iranleague_exporter.crawler.requests.get")
    def test_non_200_response(self, mock_get):
        """Test how the function handles non-200 HTTP responses."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = get_matches()
        self.assertEqual(result, [])  # Should return an empty list

    @patch("iranleague_exporter.crawler.requests.get")
    def test_empty_html_response(self, mock_get):
        """Test an empty HTML response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_get.return_value = mock_response

        result = get_matches()
        self.assertEqual(result, [])  # Should return an empty list

    @patch("iranleague_exporter.crawler.requests.get")
    def test_malformed_html_structure(self, mock_get):
        """Test how the function handles malformed HTML structure."""
        mock_html = """
        <html>
            <body>
                <div class="row">
                    <div>Week 1</div>
                    <!-- Missing second div containing the table -->
                </div>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response

        result = get_matches()
        self.assertEqual(result, [])  # Should return an empty list

    @patch("iranleague_exporter.crawler.requests.get")
    def test_rows_with_missing_data(self, mock_get):
        """Test how the function handles rows with missing data."""
        mock_html = """
        <html>
            <body>
                <div class="row">
                    <div>Week 1</div>
                    <div>
                        <table>
                            <tbody>
                                <tr>
                                    <td>Team A</td>
                                    <td>-</td>
                                    <!-- Missing opponent team -->
                                    <td></td>
                                    <td>1402/10/10</td>
                                    <td>15:30</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response

        result = get_matches()
        self.assertEqual(result, [])  # Should return an empty list

    @patch("iranleague_exporter.crawler.requests.get")
    def test_matches_with_scores(self, mock_get):
        """Test that matches with scores are excluded."""
        mock_html = """
        <html>
            <body>
                <div class="row">
                    <div>Week 1</div>
                    <div>
                        <table>
                            <tbody>
                                <tr>
                                    <td>Team A</td>
                                    <td>2 - 1</td>
                                    <td>Team B</td>
                                    <td>1402/10/10</td>
                                    <td>15:30</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response

        result = get_matches()
        self.assertEqual(result, [])  # Should return an empty list
