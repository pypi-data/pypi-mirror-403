"""
Standalone Logic Inference Engine

A simple forward-chaining inference engine that can be used as a fallback
when Pyke is not available. This provides basic logic programming capabilities
without external dependencies.
"""

import re
from typing import Any
from dataclasses import dataclass, field


@dataclass
class Fact:
    """Represents a ground fact in the knowledge base."""
    predicate: str
    args: tuple[Any, ...]

    def __hash__(self):
        return hash((self.predicate, self.args))

    def __eq__(self, other):
        if not isinstance(other, Fact):
            return False
        return self.predicate == other.predicate and self.args == other.args

    def __str__(self):
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.predicate}({args_str})"

    @classmethod
    def from_string(cls, s: str) -> "Fact":
        """Parse a fact from string like 'Predicate(arg1, arg2)'."""
        match = re.match(r'(\w+)\(([^)]*)\)', s.strip())
        if not match:
            raise ValueError(f"Invalid fact format: {s}")

        predicate = match.group(1)
        args_str = match.group(2)

        args = []
        for arg in args_str.split(','):
            arg = arg.strip()
            if arg == 'True':
                args.append(True)
            elif arg == 'False':
                args.append(False)
            elif arg.isdigit():
                args.append(int(arg))
            else:
                args.append(arg)

        return cls(predicate, tuple(args))


@dataclass
class Pattern:
    """Represents a pattern that may contain variables."""
    predicate: str
    args: tuple[Any, ...]  # Variables are strings starting with $

    def __str__(self):
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.predicate}({args_str})"

    @classmethod
    def from_string(cls, s: str) -> "Pattern":
        """Parse a pattern from string like 'Predicate($x, value)'."""
        match = re.match(r'(\w+)\(([^)]*)\)', s.strip())
        if not match:
            raise ValueError(f"Invalid pattern format: {s}")

        predicate = match.group(1)
        args_str = match.group(2)

        args = []
        for arg in args_str.split(','):
            arg = arg.strip()
            if arg == 'True':
                args.append(True)
            elif arg == 'False':
                args.append(False)
            elif arg.isdigit():
                args.append(int(arg))
            else:
                args.append(arg)  # Keep variables as strings with $

        return cls(predicate, tuple(args))

    def is_variable(self, arg: Any) -> bool:
        """Check if an argument is a variable."""
        return isinstance(arg, str) and arg.startswith('$')

    def get_variables(self) -> list[str]:
        """Get all variables in this pattern."""
        return [arg for arg in self.args if self.is_variable(arg)]

    def match(self, fact: Fact) -> dict[str, Any] | None:
        """Try to match this pattern against a fact.

        Returns variable bindings if successful, None otherwise.
        """
        if self.predicate != fact.predicate:
            return None
        if len(self.args) != len(fact.args):
            return None

        bindings = {}
        for pattern_arg, fact_arg in zip(self.args, fact.args):
            if self.is_variable(pattern_arg):
                # Variable - bind it
                if pattern_arg in bindings:
                    # Already bound - check consistency
                    if bindings[pattern_arg] != fact_arg:
                        return None
                else:
                    bindings[pattern_arg] = fact_arg
            else:
                # Constant - must match exactly
                if pattern_arg != fact_arg:
                    return None

        return bindings

    def substitute(self, bindings: dict[str, Any]) -> Fact:
        """Substitute variables with their bindings to create a fact."""
        new_args = []
        for arg in self.args:
            if self.is_variable(arg):
                if arg in bindings:
                    new_args.append(bindings[arg])
                else:
                    raise ValueError(f"Unbound variable: {arg}")
            else:
                new_args.append(arg)
        return Fact(self.predicate, tuple(new_args))


@dataclass
class Rule:
    """Represents an inference rule with premises and conclusions."""
    premises: list[Pattern]
    conclusions: list[Pattern]

    def __str__(self):
        premises_str = " && ".join(str(p) for p in self.premises)
        conclusions_str = " && ".join(str(c) for c in self.conclusions)
        return f"{premises_str} >>> {conclusions_str}"

    @classmethod
    def from_string(cls, s: str) -> "Rule":
        """Parse a rule from string like 'Premise($x) >>> Conclusion($x)'."""
        if '>>>' not in s:
            raise ValueError(f"Invalid rule format: {s}")

        premise_part, conclusion_part = s.split('>>>')

        premises = [
            Pattern.from_string(p.strip())
            for p in premise_part.split('&&')
            if p.strip()
        ]

        conclusions = [
            Pattern.from_string(c.strip())
            for c in conclusion_part.split('&&')
            if c.strip()
        ]

        return cls(premises, conclusions)


class SimpleInferenceEngine:
    """A simple forward-chaining inference engine."""

    def __init__(self):
        self.facts: set[Fact] = set()
        self.rules: list[Rule] = []

    def add_fact(self, fact: Fact | str) -> None:
        """Add a fact to the knowledge base."""
        if isinstance(fact, str):
            fact = Fact.from_string(fact)
        self.facts.add(fact)

    def add_rule(self, rule: Rule | str) -> None:
        """Add a rule to the knowledge base."""
        if isinstance(rule, str):
            rule = Rule.from_string(rule)
        self.rules.append(rule)

    def clear(self) -> None:
        """Clear all facts and rules."""
        self.facts.clear()
        self.rules.clear()

    def _find_matches(self, patterns: list[Pattern], bindings: dict[str, Any] = None) -> list[dict[str, Any]]:
        """Find all variable bindings that satisfy a list of patterns.

        Uses recursive backtracking to find all solutions.
        """
        if bindings is None:
            bindings = {}

        if not patterns:
            # All patterns matched
            return [bindings.copy()]

        pattern = patterns[0]
        remaining = patterns[1:]
        all_bindings = []

        for fact in self.facts:
            match = pattern.match(fact)
            if match is not None:
                # Check consistency with existing bindings
                consistent = True
                merged = bindings.copy()

                for var, val in match.items():
                    if var in merged:
                        if merged[var] != val:
                            consistent = False
                            break
                    else:
                        merged[var] = val

                if consistent:
                    # Recursively match remaining patterns
                    sub_bindings = self._find_matches(remaining, merged)
                    all_bindings.extend(sub_bindings)

        return all_bindings

    def forward_chain(self, max_iterations: int = 100) -> int:
        """Apply forward chaining to derive new facts.

        Returns the number of new facts derived.
        """
        total_new = 0

        for _ in range(max_iterations):
            new_facts = []

            for rule in self.rules:
                # Find all ways to satisfy the premises
                bindings_list = self._find_matches(rule.premises)

                for bindings in bindings_list:
                    # Derive conclusions
                    for conclusion in rule.conclusions:
                        try:
                            new_fact = conclusion.substitute(bindings)
                            if new_fact not in self.facts:
                                new_facts.append(new_fact)
                        except ValueError:
                            # Unbound variables - skip
                            pass

            if not new_facts:
                break

            for fact in new_facts:
                self.facts.add(fact)
            total_new += len(new_facts)

        return total_new

    def query(self, pattern: Pattern | str) -> list[dict[str, Any]]:
        """Query the knowledge base for facts matching a pattern.

        Returns all variable bindings that satisfy the query.
        """
        if isinstance(pattern, str):
            pattern = Pattern.from_string(pattern)

        # First, run forward chaining to derive all facts
        self.forward_chain()

        # Then find matches
        results = []
        for fact in self.facts:
            match = pattern.match(fact)
            if match is not None:
                results.append(match)

        return results

    def check(self, fact: Fact | str) -> bool:
        """Check if a specific fact is true in the knowledge base."""
        if isinstance(fact, str):
            fact = Fact.from_string(fact)

        self.forward_chain()
        return fact in self.facts

    def get_all_facts(self) -> list[str]:
        """Get all facts as strings."""
        return [str(f) for f in sorted(self.facts, key=str)]


class SimpleSession:
    """Session wrapper for the simple inference engine."""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.engine = SimpleInferenceEngine()
        self._facts_str: list[str] = []
        self._rules_str: list[str] = []

    def add_fact(self, fact: str) -> str:
        """Add a fact to the knowledge base."""
        fact = fact.strip()
        if not fact:
            return "Error: Empty fact"

        if '$' in fact:
            return "Error: Facts cannot contain variables. Use rules for that."

        try:
            self.engine.add_fact(fact)
            if fact not in self._facts_str:
                self._facts_str.append(fact)
            return f"Added fact: {fact}"
        except ValueError as e:
            return f"Error: {e}"

    def add_rule(self, rule: str) -> str:
        """Add a rule to the knowledge base."""
        rule = rule.strip()
        if not rule:
            return "Error: Empty rule"

        if '>>>' not in rule:
            return f"Error: Invalid rule format '{rule}'. Expected: Premise >>> Conclusion"

        try:
            self.engine.add_rule(rule)
            if rule not in self._rules_str:
                self._rules_str.append(rule)
            return f"Added rule: {rule}"
        except ValueError as e:
            return f"Error: {e}"

    def clear(self) -> str:
        """Clear the knowledge base."""
        self.engine.clear()
        self._facts_str.clear()
        self._rules_str.clear()
        return "Session cleared"

    def get_program(self) -> str:
        """Get the current program."""
        lines = []
        if self._facts_str:
            lines.append("Facts:")
            for f in self._facts_str:
                lines.append(f"  {f}")
            lines.append("")

        if self._rules_str:
            lines.append("Rules:")
            for r in self._rules_str:
                lines.append(f"  {r}")

        if not lines:
            return "No program defined yet."

        return "\n".join(lines)

    def query(self, query_str: str) -> dict[str, Any]:
        """Execute a query."""
        try:
            # Parse the query to extract expected value
            match = re.match(r'(\w+)\(([^,]+),\s*([^)]+)\)', query_str.strip())
            if not match:
                return {
                    "query": query_str,
                    "result": None,
                    "match": False,
                    "explanation": f"Invalid query format: {query_str}"
                }

            predicate = match.group(1)
            subject = match.group(2).strip()
            expected_str = match.group(3).strip()

            if expected_str == 'True':
                expected = True
            elif expected_str == 'False':
                expected = False
            else:
                expected = expected_str

            # Check if the fact exists
            fact_str = f"{predicate}({subject}, {expected_str})"
            result = self.engine.check(fact_str)

            if result:
                return {
                    "query": query_str,
                    "result": expected,
                    "match": True,
                    "explanation": f"{predicate}({subject}, {expected}) is derivable from the knowledge base."
                }
            else:
                # Check what value is derivable
                pattern_str = f"{predicate}({subject}, $value)"
                bindings = self.engine.query(pattern_str)

                if bindings:
                    actual = bindings[0].get('$value')
                    return {
                        "query": query_str,
                        "result": actual,
                        "match": actual == expected,
                        "explanation": f"Found {predicate}({subject}, {actual}). Match: {actual == expected}"
                    }
                else:
                    return {
                        "query": query_str,
                        "result": None,
                        "match": False,
                        "explanation": f"Cannot determine {predicate}({subject}, ?) from the given facts and rules."
                    }

        except Exception as e:
            return {
                "query": query_str,
                "result": None,
                "match": False,
                "explanation": f"Error: {e}"
            }

    def prove(self, goal: str) -> dict[str, Any]:
        """Prove a goal and find all bindings."""
        try:
            bindings = self.engine.query(goal)

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
                "explanation": f"Error: {e}"
            }
