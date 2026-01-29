"""
Pyke MCP Server

An MCP server that provides logic programming capabilities using the Pyke
knowledge engine. This server allows LLMs to define facts, rules, and
execute logical queries.

Based on:
- Pyke knowledge engine (https://pyke.sourceforge.net/)
- Logic-LLM Pyke implementation (https://github.com/teacherpeterpan/Logic-LLM)
"""

import logging
import os
import re
import shutil
import sys
import tempfile
from typing import Any

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (important for STDIO-based MCP servers)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("pyke-mcp")

# Check if Pyke is available
try:
    from pyke import knowledge_engine
    PYKE_AVAILABLE = True
    logger.info("Pyke knowledge engine is available")
except ImportError:
    PYKE_AVAILABLE = False
    logger.warning("Pyke not available, using fallback inference engine")

# Initialize FastMCP server
mcp = FastMCP("pyke")


class PykeSession:
    """
    Manages a Pyke knowledge engine session with facts and rules.

    This class handles:
    - Creating and managing Pyke knowledge base files (.kfb for facts, .krb for rules)
    - Parsing logic programs with predicates, facts, rules, and queries
    - Executing queries against the knowledge base
    """

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.facts: list[str] = []
        self.rules: list[str] = []
        self.predicates: list[str] = []

        # Create a unique cache directory for this session
        self.cache_dir = os.path.join(
            tempfile.gettempdir(), "pyke_mcp", session_id
        )
        os.makedirs(self.cache_dir, exist_ok=True)

        # Track compiled knowledge base directory
        self.compiled_dir = os.path.join(self.cache_dir, "compiled_krb")

        self._engine = None

    def _clean_compiled_cache(self):
        """Remove compiled knowledge base to ensure fresh compilation."""
        if os.path.exists(self.compiled_dir):
            shutil.rmtree(self.compiled_dir)

    def add_fact(self, fact: str) -> str:
        """Add a fact to the knowledge base.

        Facts should be in the format: Predicate(arg1, arg2, ...)
        Example: Human(Socrates, True)
        """
        fact = fact.strip()
        if not fact:
            return "Error: Empty fact"

        # Validate fact format (basic check)
        if not re.match(r'^\w+\([^)]+\)$', fact):
            return f"Error: Invalid fact format '{fact}'. Expected: Predicate(arg1, arg2, ...)"

        # Don't add facts with unbound variables
        if '$' in fact:
            return f"Error: Facts cannot contain variables. Use rules for that."

        if fact not in self.facts:
            self.facts.append(fact)
            return f"Added fact: {fact}"
        return f"Fact already exists: {fact}"

    def add_rule(self, rule: str) -> str:
        """Add a rule to the knowledge base.

        Rules should be in the format: Premise >>> Conclusion
        Example: Human($x, True) >>> Mortal($x, True)
        Multiple premises can be joined with &&
        Example: Furry($x, True) && Quiet($x, True) >>> White($x, True)
        """
        rule = rule.strip()
        if not rule:
            return "Error: Empty rule"

        if '>>>' not in rule:
            return f"Error: Invalid rule format '{rule}'. Expected: Premise >>> Conclusion"

        if rule not in self.rules:
            self.rules.append(rule)
            return f"Added rule: {rule}"
        return f"Rule already exists: {rule}"

    def add_predicate(self, predicate: str) -> str:
        """Add a predicate declaration."""
        predicate = predicate.strip()
        if predicate and predicate not in self.predicates:
            self.predicates.append(predicate)
            return f"Added predicate: {predicate}"
        return f"Predicate already exists: {predicate}"

    def clear(self) -> str:
        """Clear all facts, rules, and predicates."""
        self.facts = []
        self.rules = []
        self.predicates = []
        self._engine = None
        self._clean_compiled_cache()
        return "Session cleared"

    def get_program(self) -> str:
        """Get the current program as a formatted string."""
        lines = []

        if self.predicates:
            lines.append("Predicates:")
            for p in self.predicates:
                lines.append(f"  {p}")
            lines.append("")

        if self.facts:
            lines.append("Facts:")
            for f in self.facts:
                lines.append(f"  {f}")
            lines.append("")

        if self.rules:
            lines.append("Rules:")
            for r in self.rules:
                lines.append(f"  {r}")

        if not lines:
            return "No program defined yet."

        return "\n".join(lines)

    def _create_fact_file(self) -> None:
        """Create the Pyke fact file (.kfb)."""
        fact_file = os.path.join(self.cache_dir, "facts.kfb")
        with open(fact_file, 'w') as f:
            for fact in self.facts:
                # Skip facts with variables (these belong in rules)
                if '$' not in fact:
                    f.write(fact + '\n')

    def _parse_forward_rule(self, index: int, rule: str) -> str:
        """Convert a rule to Pyke's forward-chaining rule format.

        Example input: Furry($x, True) && Quiet($x, True) >>> White($x, True)
        Example output:
            fact1
                foreach
                    facts.Furry($x, True)
                    facts.Quiet($x, True)
                assert
                    facts.White($x, True)
        """
        premise, conclusion = rule.split('>>>')
        premise = premise.strip()
        conclusion = conclusion.strip()

        # Split premises by &&
        premise_list = [p.strip() for p in premise.split('&&')]

        # Split conclusions by &&
        conclusion_list = [c.strip() for c in conclusion.split('&&')]

        # Build the Pyke rule
        pyke_rule = f"fact{index}\n\tforeach"
        for p in premise_list:
            pyke_rule += f"\n\t\tfacts.{p}"
        pyke_rule += "\n\tassert"
        for c in conclusion_list:
            pyke_rule += f"\n\t\tfacts.{c}"

        return pyke_rule

    def _create_rule_file(self) -> None:
        """Create the Pyke rule file (.krb)."""
        rule_file = os.path.join(self.cache_dir, "rules.krb")
        pyke_rules = []

        for idx, rule in enumerate(self.rules):
            pyke_rules.append(self._parse_forward_rule(idx + 1, rule))

        with open(rule_file, 'w') as f:
            f.write('\n\n'.join(pyke_rules))

    def _initialize_engine(self):
        """Initialize the Pyke knowledge engine or fallback to simple engine."""
        if not PYKE_AVAILABLE:
            # Use fallback simple inference engine
            return self._initialize_fallback_engine()

        from pyke import knowledge_engine

        # Clean and recreate files
        self._clean_compiled_cache()
        self._create_fact_file()
        self._create_rule_file()

        # Create and initialize the engine
        self._engine = knowledge_engine.engine(self.cache_dir)
        self._engine.reset()
        self._engine.activate('rules')
        self._engine.get_kb('facts')

        return self._engine

    def _initialize_fallback_engine(self):
        """Initialize the fallback simple inference engine."""
        from .engine import SimpleInferenceEngine

        engine = SimpleInferenceEngine()

        # Load facts
        for fact in self.facts:
            engine.add_fact(fact)

        # Load rules
        for rule in self.rules:
            engine.add_rule(rule)

        self._fallback_engine = engine
        return engine

    def _parse_query(self, query: str) -> tuple[str, str, Any]:
        """Parse a query into (predicate, subject, expected_value).

        Example: Mortal(Socrates, True) -> ('Mortal', 'Socrates', True)
        """
        pattern = r'(\w+)\(([^,]+),\s*([^)]+)\)'
        match = re.match(pattern, query.strip())

        if match:
            predicate = match.group(1)
            subject = match.group(2).strip()
            value_str = match.group(3).strip()

            # Convert value
            if value_str == 'True':
                value = True
            elif value_str == 'False':
                value = False
            else:
                value = value_str

            return predicate, subject, value
        else:
            raise ValueError(f"Invalid query format: {query}")

    def _check_predicate(self, subject: str, predicate: str, engine) -> Any:
        """Check a specific predicate for a subject.

        Returns the value(s) found, or None if not found.
        """
        results = []

        # Check facts
        try:
            with engine.prove_goal(f'facts.{predicate}({subject}, $label)') as gen:
                for vars, plan in gen:
                    results.append(vars['label'])
        except Exception:
            pass

        # Check derived rules
        try:
            with engine.prove_goal(f'rules.{predicate}({subject}, $label)') as gen:
                for vars, plan in gen:
                    results.append(vars['label'])
        except Exception:
            pass

        if len(results) == 0:
            return None
        elif len(results) == 1:
            return results[0]
        else:
            # Multiple results - return combined
            return results

    def query(self, query_str: str) -> dict[str, Any]:
        """Execute a query against the knowledge base.

        Query format: Predicate(Subject, ExpectedValue)
        Example: Mortal(Socrates, True)

        Returns a dict with:
        - query: the original query
        - result: the derived value (or None if not found)
        - match: whether the result matches the expected value
        - explanation: human-readable explanation
        """
        if not self.facts and not self.rules:
            return {
                "query": query_str,
                "result": None,
                "match": False,
                "explanation": "No facts or rules defined. Add some first."
            }

        try:
            if not PYKE_AVAILABLE:
                # Use fallback engine
                return self._query_fallback(query_str)

            engine = self._initialize_engine()
            predicate, subject, expected_value = self._parse_query(query_str)
            result = self._check_predicate(subject, predicate, engine)

            if result is None:
                return {
                    "query": query_str,
                    "result": None,
                    "match": False,
                    "explanation": f"Cannot determine {predicate}({subject}, ?) from the given facts and rules."
                }

            match = (result == expected_value)

            return {
                "query": query_str,
                "result": result,
                "match": match,
                "explanation": f"{predicate}({subject}, {result}) is {'True' if result else 'False'}. "
                              f"The query {'matches' if match else 'does not match'} the expected value."
            }

        except Exception as e:
            return {
                "query": query_str,
                "result": None,
                "match": False,
                "explanation": f"Error executing query: {str(e)}"
            }

    def _query_fallback(self, query_str: str) -> dict[str, Any]:
        """Execute query using the fallback simple engine."""
        from .engine import SimpleSession

        # Create a simple session and load current state
        simple_session = SimpleSession(self.session_id + "_fallback")
        for fact in self.facts:
            simple_session.add_fact(fact)
        for rule in self.rules:
            simple_session.add_rule(rule)

        return simple_session.query(query_str)

    def prove(self, goal: str) -> dict[str, Any]:
        """Prove a goal and return all matching bindings.

        Goal format: Predicate(Subject, $variable) or Predicate($x, $y)
        Example: Mortal($who, True) - finds all mortals

        Returns a dict with:
        - goal: the original goal
        - bindings: list of variable bindings that satisfy the goal
        - success: whether any bindings were found
        """
        if not self.facts and not self.rules:
            return {
                "goal": goal,
                "bindings": [],
                "success": False,
                "explanation": "No facts or rules defined. Add some first."
            }

        try:
            if not PYKE_AVAILABLE:
                # Use fallback engine
                return self._prove_fallback(goal)

            engine = self._initialize_engine()
            bindings = []

            # Try to prove from facts
            try:
                with engine.prove_goal(f'facts.{goal}') as gen:
                    for vars, plan in gen:
                        bindings.append(dict(vars))
            except Exception:
                pass

            # Try to prove from rules
            try:
                with engine.prove_goal(f'rules.{goal}') as gen:
                    for vars, plan in gen:
                        if dict(vars) not in bindings:
                            bindings.append(dict(vars))
            except Exception:
                pass

            return {
                "goal": goal,
                "bindings": bindings,
                "success": len(bindings) > 0,
                "explanation": f"Found {len(bindings)} solution(s)" if bindings else "No solutions found"
            }

        except Exception as e:
            return {
                "goal": goal,
                "bindings": [],
                "success": False,
                "explanation": f"Error proving goal: {str(e)}"
            }

    def _prove_fallback(self, goal: str) -> dict[str, Any]:
        """Prove goal using the fallback simple engine."""
        from .engine import SimpleSession

        # Create a simple session and load current state
        simple_session = SimpleSession(self.session_id + "_fallback")
        for fact in self.facts:
            simple_session.add_fact(fact)
        for rule in self.rules:
            simple_session.add_rule(rule)

        return simple_session.prove(goal)


# Global session storage
_sessions: dict[str, PykeSession] = {}


def get_session(session_id: str = "default") -> PykeSession:
    """Get or create a session by ID."""
    if session_id not in _sessions:
        _sessions[session_id] = PykeSession(session_id)
    return _sessions[session_id]


# ============================================================================
# MCP Tool Definitions
# ============================================================================

@mcp.tool()
def add_fact(fact: str, session_id: str = "default") -> str:
    """Add a fact to the Pyke knowledge base.

    Facts represent ground truths about entities in your domain.

    Args:
        fact: A fact in the format Predicate(arg1, arg2, ...).
              Example: Human(Socrates, True) or Parent(John, Mary)
        session_id: Optional session identifier for managing multiple knowledge bases

    Returns:
        Confirmation message or error description

    Examples:
        - Human(Socrates, True) - Socrates is human
        - Mortal(Plato, True) - Plato is mortal
        - Parent(John, Mary) - John is a parent of Mary
        - Color(Sky, Blue) - The sky is blue
    """
    session = get_session(session_id)
    return session.add_fact(fact)


@mcp.tool()
def add_rule(rule: str, session_id: str = "default") -> str:
    """Add an inference rule to the Pyke knowledge base.

    Rules define logical implications using forward chaining.
    Variables are denoted with $ prefix (e.g., $x, $person).

    Args:
        rule: A rule in the format: Premise >>> Conclusion
              Multiple premises can be joined with &&
              Example: Human($x, True) >>> Mortal($x, True)
        session_id: Optional session identifier

    Returns:
        Confirmation message or error description

    Examples:
        - Human($x, True) >>> Mortal($x, True)
          "All humans are mortal"

        - Parent($x, $y) && Parent($y, $z) >>> Grandparent($x, $z)
          "If X is parent of Y and Y is parent of Z, then X is grandparent of Z"

        - Furry($x, True) && Quiet($x, True) >>> White($x, True)
          "Furry and quiet things are white"
    """
    session = get_session(session_id)
    return session.add_rule(rule)


@mcp.tool()
def add_facts_and_rules(
    facts: list[str] | None = None,
    rules: list[str] | None = None,
    session_id: str = "default"
) -> str:
    """Add multiple facts and rules to the knowledge base at once.

    This is a convenience method for bulk loading a logic program.

    Args:
        facts: List of facts to add
        rules: List of rules to add
        session_id: Optional session identifier

    Returns:
        Summary of what was added

    Example:
        facts: ["Human(Socrates, True)", "Human(Plato, True)"]
        rules: ["Human($x, True) >>> Mortal($x, True)"]
    """
    session = get_session(session_id)
    results = []

    if facts:
        for fact in facts:
            result = session.add_fact(fact)
            results.append(result)

    if rules:
        for rule in rules:
            result = session.add_rule(rule)
            results.append(result)

    return "\n".join(results) if results else "No facts or rules provided"


@mcp.tool()
def query(query_str: str, session_id: str = "default") -> str:
    """Execute a query to check if a fact can be derived.

    Queries check whether a specific predicate holds for given arguments,
    using both direct facts and derived knowledge from rules.

    Args:
        query_str: Query in format Predicate(Subject, ExpectedValue)
                   Example: Mortal(Socrates, True)
        session_id: Optional session identifier

    Returns:
        Query result with explanation

    Examples:
        - Mortal(Socrates, True) - "Is Socrates mortal?"
        - Human(Plato, True) - "Is Plato human?"
        - Grandparent(John, Alice, True) - "Is John a grandparent of Alice?"
    """
    session = get_session(session_id)
    result = session.query(query_str)

    output = [
        f"Query: {result['query']}",
        f"Result: {result['result']}",
        f"Match: {result['match']}",
        f"Explanation: {result['explanation']}"
    ]

    return "\n".join(output)


@mcp.tool()
def prove_goal(goal: str, session_id: str = "default") -> str:
    """Prove a goal and find all variable bindings that satisfy it.

    Unlike query(), this finds ALL solutions with variable bindings.
    Use $variable syntax for variables you want to find values for.

    Args:
        goal: Goal pattern with variables, e.g., Mortal($who, True)
        session_id: Optional session identifier

    Returns:
        All variable bindings that satisfy the goal

    Examples:
        - Mortal($who, True) - "Who is mortal?"
        - Parent($parent, Mary) - "Who are Mary's parents?"
        - Grandparent(John, $grandchild) - "Who are John's grandchildren?"
    """
    session = get_session(session_id)
    result = session.prove(goal)

    output = [
        f"Goal: {result['goal']}",
        f"Success: {result['success']}",
        f"Explanation: {result['explanation']}"
    ]

    if result['bindings']:
        output.append("Bindings:")
        for i, binding in enumerate(result['bindings'], 1):
            binding_str = ", ".join(f"{k}={v}" for k, v in binding.items())
            output.append(f"  {i}. {binding_str}")

    return "\n".join(output)


@mcp.tool()
def get_program(session_id: str = "default") -> str:
    """Get the current logic program (facts and rules).

    Returns the complete knowledge base content for review.

    Args:
        session_id: Optional session identifier

    Returns:
        Formatted string showing all predicates, facts, and rules
    """
    session = get_session(session_id)
    return session.get_program()


@mcp.tool()
def clear_program(session_id: str = "default") -> str:
    """Clear all facts, rules, and predicates from the knowledge base.

    This resets the session to an empty state.

    Args:
        session_id: Optional session identifier

    Returns:
        Confirmation message
    """
    session = get_session(session_id)
    return session.clear()


@mcp.tool()
def load_logic_program(program: str, session_id: str = "default") -> str:
    """Load a complete logic program from a formatted string.

    Parses and loads a program with Predicates, Facts, Rules, and Query sections.
    This format is compatible with Logic-LLM style programs.

    Args:
        program: A formatted logic program string with sections:
                 Predicates: (optional)
                 Facts:
                 Rules:
                 Query: (optional, for immediate execution)
        session_id: Optional session identifier

    Returns:
        Summary of loaded program and optional query result

    Example program:
        Predicates:
        Human(x, bool)
        Mortal(x, bool)

        Facts:
        Human(Socrates, True)
        Human(Plato, True)

        Rules:
        Human($x, True) >>> Mortal($x, True)

        Query:
        Mortal(Socrates, True)
    """
    session = get_session(session_id)
    session.clear()

    results = []

    # Parse sections
    keywords = ['Query:', 'Rules:', 'Facts:', 'Predicates:']
    sections = {}
    current_section = None
    current_content = []

    for line in program.split('\n'):
        line = line.strip()

        # Check if this line starts a new section
        section_found = None
        for keyword in keywords:
            if line.startswith(keyword):
                section_found = keyword[:-1]  # Remove the colon
                break

        if section_found:
            # Save previous section
            if current_section:
                sections[current_section] = current_content
            current_section = section_found
            current_content = []
        elif current_section and line:
            # Remove any trailing comments (:::)
            if ':::' in line:
                line = line.split(':::')[0].strip()
            if line:
                current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = current_content

    # Load predicates
    if 'Predicates' in sections:
        for pred in sections['Predicates']:
            session.add_predicate(pred)
        results.append(f"Loaded {len(sections['Predicates'])} predicates")

    # Load facts
    if 'Facts' in sections:
        for fact in sections['Facts']:
            session.add_fact(fact)
        results.append(f"Loaded {len(sections['Facts'])} facts")

    # Load rules
    if 'Rules' in sections:
        for rule in sections['Rules']:
            session.add_rule(rule)
        results.append(f"Loaded {len(sections['Rules'])} rules")

    # Execute query if present
    if 'Query' in sections and sections['Query']:
        query_str = sections['Query'][0]
        query_result = session.query(query_str)
        results.append(f"\nQuery: {query_str}")
        results.append(f"Result: {query_result['result']}")
        results.append(f"Match: {query_result['match']}")
        results.append(f"Explanation: {query_result['explanation']}")

    return "\n".join(results) if results else "No content found in program"


@mcp.tool()
def list_sessions() -> str:
    """List all active Pyke sessions.

    Returns:
        List of session IDs and their sizes
    """
    if not _sessions:
        return "No active sessions"

    output = ["Active sessions:"]
    for session_id, session in _sessions.items():
        output.append(
            f"  - {session_id}: {len(session.facts)} facts, {len(session.rules)} rules"
        )

    return "\n".join(output)


@mcp.tool()
def delete_session(session_id: str) -> str:
    """Delete a specific session.

    Args:
        session_id: The session to delete

    Returns:
        Confirmation message
    """
    if session_id in _sessions:
        session = _sessions[session_id]
        session.clear()
        # Clean up cache directory
        if os.path.exists(session.cache_dir):
            shutil.rmtree(session.cache_dir)
        del _sessions[session_id]
        return f"Session '{session_id}' deleted"
    return f"Session '{session_id}' not found"


def main():
    """Run the Pyke MCP server."""
    logger.info("Starting Pyke MCP server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
