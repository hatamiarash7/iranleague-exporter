"""Tests for the crawler module."""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

import jdatetime

from iranleague_exporter.config import Language, reset_config
from iranleague_exporter.crawler import (
    HTTPError,
    ParseError,
    _parse_date_time,
    _parse_matches_html,
    get_matches,
)


class TestGetMatches(unittest.TestCase):
    def setUp(self):
        """Reset config before each test."""
        reset_config()

    def tearDown(self):
        """Reset config after each test."""
        reset_config()

    @patch("iranleague_exporter.crawler.requests.Session")
    def test_successful_response_with_valid_data(self, mock_session_class):
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

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        date = jdatetime.date(day=10, month=10, year=1402).togregorian()
        time = "15:30"

        result = get_matches(lang="EN")
        expected_result = [
            {
                "teams": "Team-A vs Team-B",
                "timestamp": int(
                    datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").timestamp()
                ),
            }
        ]

        self.assertEqual(result, expected_result)

    @patch("iranleague_exporter.crawler.requests.Session")
    def test_successful_response_with_valid_data_fa(self, mock_session_class):
        """Test a successful response with valid HTML content for FA language."""
        mock_html = """
        <html>
            <body>
                <div class="row">
                    <div>Week 1</div>
                    <div>
                        <table>
                            <tbody>
                                <tr>
                                    <td>تیم اول</td>
                                    <td>-</td>
                                    <td>تیم دوم</td>
                                    <td>1402/10/10</td>
                                    <td>15:30</td>
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

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        date = jdatetime.date(day=10, month=10, year=1402).togregorian()
        time = "15:30"

        result = get_matches(lang="FA")
        expected_result = [
            {
                "teams": "تیم اول vs تیم دوم",
                "timestamp": int(
                    datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").timestamp()
                ),
            }
        ]

        self.assertEqual(result, expected_result)

    @patch("iranleague_exporter.crawler.requests.Session")
    def test_non_200_response(self, mock_session_class):
        """Test how the function handles non-200 HTTP responses."""
        mock_response = Mock()
        mock_response.status_code = 404

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        with self.assertRaises(HTTPError) as context:
            get_matches(lang="EN")
        self.assertEqual(context.exception.status_code, 404)

    @patch("iranleague_exporter.crawler.requests.Session")
    def test_empty_html_response(self, mock_session_class):
        """Test an empty HTML response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = get_matches(lang="EN")
        self.assertEqual(result, [])

    @patch("iranleague_exporter.crawler.requests.Session")
    def test_malformed_html_structure(self, mock_session_class):
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

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = get_matches(lang="EN")
        self.assertEqual(result, [])

    @patch("iranleague_exporter.crawler.requests.Session")
    def test_rows_with_missing_data(self, mock_session_class):
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

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = get_matches(lang="EN")
        self.assertEqual(result, [])

    @patch("iranleague_exporter.crawler.requests.Session")
    def test_matches_with_scores(self, mock_session_class):
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

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = get_matches(lang="EN")
        self.assertEqual(result, [])


class TestParseDatetime(unittest.TestCase):
    """Tests for the _parse_date_time function."""

    def test_valid_date_time(self):
        """Test parsing valid Persian date and time."""
        timestamp = _parse_date_time("1402/10/10", "15:30")
        date = jdatetime.date(day=10, month=10, year=1402).togregorian()
        expected = int(datetime.strptime(f"{date} 15:30", "%Y-%m-%d %H:%M").timestamp())
        self.assertEqual(timestamp, expected)

    def test_empty_time_defaults_to_midnight(self):
        """Test that empty time defaults to 00:00."""
        timestamp = _parse_date_time("1402/10/10", "")
        date = jdatetime.date(day=10, month=10, year=1402).togregorian()
        expected = int(datetime.strptime(f"{date} 00:00", "%Y-%m-%d %H:%M").timestamp())
        self.assertEqual(timestamp, expected)

    def test_invalid_date_format(self):
        """Test that invalid date format raises ParseError."""
        with self.assertRaises(ParseError):
            _parse_date_time("1402-10-10", "15:30")

    def test_incomplete_date(self):
        """Test that incomplete date raises ParseError."""
        with self.assertRaises(ParseError):
            _parse_date_time("1402/10", "15:30")


class TestParseMatchesHtml(unittest.TestCase):
    """Tests for the _parse_matches_html function."""

    def test_empty_html(self):
        """Test parsing empty HTML."""
        result = _parse_matches_html("", Language.EN)
        self.assertEqual(result, [])

    def test_whitespace_only_html(self):
        """Test parsing whitespace-only HTML."""
        result = _parse_matches_html("   \n\t  ", Language.EN)
        self.assertEqual(result, [])

    def test_html_without_weeks(self):
        """Test HTML without any week rows."""
        html = "<html><body><div>No matches</div></body></html>"
        result = _parse_matches_html(html, Language.EN)
        self.assertEqual(result, [])


class TestLanguageEnum(unittest.TestCase):
    """Tests for language handling."""

    @patch("iranleague_exporter.crawler.requests.Session")
    def test_language_enum_input(self, mock_session_class):
        """Test that Language enum is accepted directly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html></html>"

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = get_matches(lang=Language.FA)
        self.assertEqual(result, [])

    @patch("iranleague_exporter.crawler.requests.Session")
    def test_invalid_language_defaults_to_en(self, mock_session_class):
        """Test that invalid language defaults to EN."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html></html>"

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        # Should not raise and should default to EN
        result = get_matches(lang="INVALID")
        self.assertEqual(result, [])
