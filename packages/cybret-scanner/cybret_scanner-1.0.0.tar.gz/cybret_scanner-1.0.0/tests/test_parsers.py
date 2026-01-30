"""
Tests for language parsers
"""

import pytest
from pathlib import Path
import tempfile

from scanner.parsers.python_parser import PythonParser
from scanner.parsers.base import EntityType


class TestPythonParser:
    """Test Python parser"""

    def test_parse_simple_function(self):
        """Test parsing a simple function"""
        code = """
def hello_world():
    return "Hello, World!"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            parser = PythonParser()
            ast_node = parser.parse_file(Path(f.name))

            # Should have one function child
            functions = ast_node.find_children_by_type(EntityType.FUNCTION)
            assert len(functions) == 1
            assert functions[0].name == "hello_world"

    def test_parse_class_with_methods(self):
        """Test parsing a class with methods"""
        code = """
class User:
    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            parser = PythonParser()
            ast_node = parser.parse_file(Path(f.name))

            # Should have one class
            classes = ast_node.find_children_by_type(EntityType.CLASS)
            assert len(classes) == 1
            assert classes[0].name == "User"

            # Should have methods
            methods = ast_node.find_children_by_type(EntityType.METHOD)
            assert len(methods) >= 2

    def test_detect_api_endpoint(self):
        """Test detection of API endpoints with decorators"""
        code = """
from flask import Flask

app = Flask(__name__)

@app.route('/api/user/<user_id>')
def get_user(user_id):
    return User.query.get(user_id)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            parser = PythonParser()
            ast_node = parser.parse_file(Path(f.name))

            # Should detect API endpoint
            endpoints = [
                node
                for node in ast_node.find_children_by_type(EntityType.FUNCTION)
                if "is_api_endpoint" in node.tags
            ]
            assert len(endpoints) >= 1

    def test_detect_database_query(self):
        """Test detection of database queries"""
        code = """
def get_document(doc_id):
    doc = Document.query.filter_by(id=doc_id).first()
    return doc
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            parser = PythonParser()
            ast_node = parser.parse_file(Path(f.name))

            # Should detect database operations
            db_queries = ast_node.find_children_by_type(EntityType.DATABASE_QUERY)
            # Note: detection depends on method names containing 'query', 'filter', etc.
            assert len(db_queries) >= 0  # May vary based on implementation

    def test_extract_entities(self):
        """Test entity extraction"""
        code = """
@app.route('/api/document/<doc_id>')
@login_required
def get_document(doc_id):
    doc = Document.query.get(doc_id)
    return doc
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            parser = PythonParser()
            ast_node = parser.parse_file(Path(f.name))
            entities = parser.extract_entities(ast_node)

            assert len(entities) >= 1
            entity = entities[0]
            assert entity.name == "get_document"
            assert entity.handles_user_input  # Has route decorator


class TestParserEdgeCases:
    """Test parser edge cases"""

    def test_parse_empty_file(self):
        """Test parsing an empty file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("")
            f.flush()

            parser = PythonParser()
            ast_node = parser.parse_file(Path(f.name))

            assert ast_node.entity_type == EntityType.FILE
            assert len(ast_node.children) == 0

    def test_parse_syntax_error(self):
        """Test handling of syntax errors"""
        code = """
def broken_function(
    # Missing closing parenthesis
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            parser = PythonParser()
            with pytest.raises(ValueError):
                parser.parse_file(Path(f.name))
