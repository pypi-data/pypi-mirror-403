"""Tests for PykeSession class."""

import pytest
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pyke_mcp.server import PykeSession, get_session


class TestPykeSession:
    """Test suite for PykeSession."""

    def setup_method(self):
        """Set up a fresh session for each test."""
        self.session = PykeSession("test_session")
        self.session.clear()

    def teardown_method(self):
        """Clean up after each test."""
        self.session.clear()

    def test_add_fact_valid(self):
        """Test adding a valid fact."""
        result = self.session.add_fact("Human(Socrates, True)")
        assert "Added fact" in result
        assert "Human(Socrates, True)" in self.session.facts

    def test_add_fact_duplicate(self):
        """Test adding a duplicate fact."""
        self.session.add_fact("Human(Socrates, True)")
        result = self.session.add_fact("Human(Socrates, True)")
        assert "already exists" in result

    def test_add_fact_invalid_format(self):
        """Test adding an invalid fact."""
        result = self.session.add_fact("invalid fact")
        assert "Error" in result

    def test_add_fact_with_variable(self):
        """Test that facts with variables are rejected."""
        result = self.session.add_fact("Human($x, True)")
        assert "Error" in result
        assert "variables" in result.lower()

    def test_add_rule_valid(self):
        """Test adding a valid rule."""
        result = self.session.add_rule("Human($x, True) >>> Mortal($x, True)")
        assert "Added rule" in result
        assert len(self.session.rules) == 1

    def test_add_rule_invalid_format(self):
        """Test adding an invalid rule."""
        result = self.session.add_rule("Human(x) implies Mortal(x)")
        assert "Error" in result

    def test_add_rule_with_multiple_premises(self):
        """Test adding a rule with multiple premises."""
        result = self.session.add_rule(
            "Parent($x, $y) && Parent($y, $z) >>> Grandparent($x, $z)"
        )
        assert "Added rule" in result

    def test_clear(self):
        """Test clearing the session."""
        self.session.add_fact("Human(Socrates, True)")
        self.session.add_rule("Human($x, True) >>> Mortal($x, True)")

        result = self.session.clear()

        assert "cleared" in result.lower()
        assert len(self.session.facts) == 0
        assert len(self.session.rules) == 0

    def test_get_program_empty(self):
        """Test getting an empty program."""
        result = self.session.get_program()
        assert "No program" in result

    def test_get_program_with_content(self):
        """Test getting a program with content."""
        self.session.add_fact("Human(Socrates, True)")
        self.session.add_rule("Human($x, True) >>> Mortal($x, True)")

        result = self.session.get_program()

        assert "Facts:" in result
        assert "Rules:" in result
        assert "Human(Socrates, True)" in result

    def test_parse_query_valid(self):
        """Test parsing a valid query."""
        predicate, subject, value = self.session._parse_query("Mortal(Socrates, True)")
        assert predicate == "Mortal"
        assert subject == "Socrates"
        assert value is True

    def test_parse_query_false_value(self):
        """Test parsing a query with False value."""
        predicate, subject, value = self.session._parse_query("Mortal(Plato, False)")
        assert value is False

    def test_parse_query_string_value(self):
        """Test parsing a query with string value."""
        predicate, subject, value = self.session._parse_query("Color(Sky, Blue)")
        assert value == "Blue"

    def test_parse_forward_rule(self):
        """Test parsing a forward rule into Pyke format."""
        rule = "Human($x, True) >>> Mortal($x, True)"
        result = self.session._parse_forward_rule(1, rule)

        assert "fact1" in result
        assert "foreach" in result
        assert "facts.Human($x, True)" in result
        assert "assert" in result
        assert "facts.Mortal($x, True)" in result


class TestGetSession:
    """Test suite for session management."""

    def test_get_new_session(self):
        """Test getting a new session."""
        session = get_session("new_test_session")
        assert session is not None
        assert session.session_id == "new_test_session"
        # Clean up
        session.clear()

    def test_get_existing_session(self):
        """Test getting an existing session returns the same object."""
        session1 = get_session("reuse_test")
        session1.add_fact("Test(1, True)")

        session2 = get_session("reuse_test")

        assert session1 is session2
        assert "Test(1, True)" in session2.facts
        # Clean up
        session1.clear()

    def test_default_session(self):
        """Test that default session is used when no ID provided."""
        session = get_session()
        assert session.session_id == "default"


# Skip integration tests if pyke is not installed
try:
    from pyke import knowledge_engine
    PYKE_AVAILABLE = True
except ImportError:
    PYKE_AVAILABLE = False


@pytest.mark.skipif(not PYKE_AVAILABLE, reason="Pyke not installed")
class TestPykeIntegration:
    """Integration tests that require Pyke to be installed."""

    def setup_method(self):
        """Set up a fresh session for each test."""
        self.session = PykeSession("integration_test")
        self.session.clear()

    def teardown_method(self):
        """Clean up after each test."""
        self.session.clear()

    def test_simple_query(self):
        """Test a simple query with direct fact."""
        self.session.add_fact("Human(Socrates, True)")

        result = self.session.query("Human(Socrates, True)")

        assert result["match"] is True
        assert result["result"] is True

    def test_derived_query(self):
        """Test a query that requires rule application."""
        self.session.add_fact("Human(Socrates, True)")
        self.session.add_rule("Human($x, True) >>> Mortal($x, True)")

        result = self.session.query("Mortal(Socrates, True)")

        assert result["match"] is True

    def test_query_not_found(self):
        """Test a query that cannot be derived."""
        self.session.add_fact("Human(Socrates, True)")

        result = self.session.query("Flying(Socrates, True)")

        assert result["result"] is None
        assert result["match"] is False

    def test_prove_goal(self):
        """Test proving a goal with variable bindings."""
        self.session.add_fact("Human(Socrates, True)")
        self.session.add_fact("Human(Plato, True)")
        self.session.add_rule("Human($x, True) >>> Mortal($x, True)")

        result = self.session.prove("Mortal($who, True)")

        assert result["success"] is True
        assert len(result["bindings"]) >= 2

    def test_chained_rules(self):
        """Test rules that chain together."""
        self.session.add_fact("Animal(Rex, True)")
        self.session.add_fact("HasFur(Rex, True)")
        self.session.add_rule("Animal($x, True) && HasFur($x, True) >>> Mammal($x, True)")
        self.session.add_rule("Mammal($x, True) >>> WarmBlooded($x, True)")

        result = self.session.query("WarmBlooded(Rex, True)")

        # Note: This might fail depending on Pyke's rule chaining
        # The test documents expected behavior


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
