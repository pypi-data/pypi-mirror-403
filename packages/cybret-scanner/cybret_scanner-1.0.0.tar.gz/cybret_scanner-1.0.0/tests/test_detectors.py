"""
Tests for vulnerability detectors
"""

import pytest
from unittest.mock import Mock, MagicMock

from scanner.detectors.idor import IDORDetector
from scanner.detectors.auth_bypass import AuthBypassDetector
from scanner.detectors.base import VulnerabilitySeverity


class TestIDORDetector:
    """Test IDOR vulnerability detector"""

    def test_detector_initialization(self):
        """Test detector initialization"""
        mock_driver = Mock()
        detector = IDORDetector(mock_driver, "neo4j")

        assert detector.name == "IDORDetector"
        assert len(detector.vulnerabilities) == 0

    def test_generate_vuln_id(self):
        """Test vulnerability ID generation"""
        mock_driver = Mock()
        detector = IDORDetector(mock_driver, "neo4j")

        vuln_id_1 = detector._generate_vuln_id("/app/api.py", 42, "IDOR_DIRECT_DB")
        vuln_id_2 = detector._generate_vuln_id("/app/api.py", 42, "IDOR_DIRECT_DB")
        vuln_id_3 = detector._generate_vuln_id("/app/api.py", 43, "IDOR_DIRECT_DB")

        # Same inputs should generate same ID
        assert vuln_id_1 == vuln_id_2

        # Different inputs should generate different ID
        assert vuln_id_1 != vuln_id_3

        # ID should start with correct prefix
        assert vuln_id_1.startswith("IDOR-")


class TestAuthBypassDetector:
    """Test Authentication Bypass detector"""

    def test_detector_initialization(self):
        """Test detector initialization"""
        mock_driver = Mock()
        detector = AuthBypassDetector(mock_driver, "neo4j")

        assert detector.name == "AuthBypassDetector"
        assert len(detector.vulnerabilities) == 0

    def test_generate_vuln_id(self):
        """Test vulnerability ID generation"""
        mock_driver = Mock()
        detector = AuthBypassDetector(mock_driver, "neo4j")

        vuln_id = detector._generate_vuln_id("/app/auth.py", 100, "AUTH_DEBUG_BYPASS")

        assert vuln_id.startswith("AUTH-")
        assert len(vuln_id) > 5


class TestVulnerabilityDetection:
    """Integration tests for vulnerability detection"""

    @pytest.fixture
    def mock_neo4j_session(self):
        """Mock Neo4j session"""
        session = Mock()
        session.run = Mock(return_value=iter([]))
        return session

    def test_idor_detector_detect_method(self, mock_neo4j_session):
        """Test IDOR detector detect method"""
        mock_driver = Mock()
        mock_driver.session = Mock(return_value=mock_neo4j_session)

        detector = IDORDetector(mock_driver, "neo4j")

        # Mock context manager
        mock_neo4j_session.__enter__ = Mock(return_value=mock_neo4j_session)
        mock_neo4j_session.__exit__ = Mock(return_value=False)

        vulnerabilities = detector.detect("test_scan_123")

        # Should return a list (even if empty without real data)
        assert isinstance(vulnerabilities, list)

    def test_auth_bypass_detector_detect_method(self, mock_neo4j_session):
        """Test Auth Bypass detector detect method"""
        mock_driver = Mock()
        mock_driver.session = Mock(return_value=mock_neo4j_session)

        detector = AuthBypassDetector(mock_driver, "neo4j")

        # Mock context manager
        mock_neo4j_session.__enter__ = Mock(return_value=mock_neo4j_session)
        mock_neo4j_session.__exit__ = Mock(return_value=False)

        vulnerabilities = detector.detect("test_scan_123")

        # Should return a list
        assert isinstance(vulnerabilities, list)
