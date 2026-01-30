"""
CYBRET AI Logic Vulnerability Scanner

A multi-language static analysis security scanner that builds knowledge graphs
to detect complex logic vulnerabilities.
"""

__version__ = "1.0.0"
__author__ = "CYBRET AI"

from scanner.parsers.base import BaseParser
from scanner.graph.builder import GraphBuilder
from scanner.detectors.base import BaseDetector

__all__ = ["BaseParser", "GraphBuilder", "BaseDetector"]
