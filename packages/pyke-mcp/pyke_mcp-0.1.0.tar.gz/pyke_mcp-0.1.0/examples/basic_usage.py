#!/usr/bin/env python3
"""
Basic usage example for Pyke MCP Server.

This script demonstrates how to use the PykeSession class directly,
without going through the MCP protocol. This is useful for testing
and understanding the logic programming capabilities.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pyke_mcp.server import PykeSession


def example_classic_syllogism():
    """Classic Socrates syllogism example."""
    print("=" * 60)
    print("Example 1: Classic Syllogism")
    print("=" * 60)

    session = PykeSession("syllogism")

    # Add facts
    print("\nAdding facts:")
    print(f"  {session.add_fact('Human(Socrates, True)')}")
    print(f"  {session.add_fact('Human(Plato, True)')}")
    print(f"  {session.add_fact('Human(Aristotle, True)')}")

    # Add rule
    print("\nAdding rule:")
    print(f"  {session.add_rule('Human($x, True) >>> Mortal($x, True)')}")

    # Show program
    print("\nCurrent program:")
    print(session.get_program())

    # Query
    print("\nQuery: Is Socrates mortal?")
    result = session.query("Mortal(Socrates, True)")
    print(f"  Result: {result['result']}")
    print(f"  Match: {result['match']}")
    print(f"  Explanation: {result['explanation']}")

    # Prove goal - find all mortals
    print("\nGoal: Who is mortal?")
    result = session.prove("Mortal($who, True)")
    print(f"  Success: {result['success']}")
    print(f"  Bindings: {result['bindings']}")

    session.clear()


def example_family_relationships():
    """Family relationship reasoning example."""
    print("\n" + "=" * 60)
    print("Example 2: Family Relationships")
    print("=" * 60)

    session = PykeSession("family")

    # Add facts about parent relationships
    print("\nAdding facts:")
    facts = [
        "Parent(Alice, Bob)",
        "Parent(Alice, Carol)",
        "Parent(Bob, David)",
        "Parent(Bob, Eve)",
        "Parent(Carol, Frank)",
    ]
    for fact in facts:
        print(f"  {session.add_fact(fact)}")

    # Add rules
    print("\nAdding rules:")
    rules = [
        "Parent($x, $y) && Parent($y, $z) >>> Grandparent($x, $z)",
        "Parent($x, $y) && Parent($x, $z) >>> Sibling($y, $z)",
    ]
    for rule in rules:
        print(f"  {session.add_rule(rule)}")

    # Show program
    print("\nCurrent program:")
    print(session.get_program())

    # Query grandparent relationship
    print("\nQuery: Is Alice a grandparent of David?")
    result = session.query("Grandparent(Alice, David)")
    print(f"  Result: {result['result']}")
    print(f"  Explanation: {result['explanation']}")

    # Find all grandchildren of Alice
    print("\nGoal: Who are Alice's grandchildren?")
    result = session.prove("Grandparent(Alice, $grandchild)")
    print(f"  Success: {result['success']}")
    if result['bindings']:
        for binding in result['bindings']:
            print(f"  - {binding}")

    session.clear()


def example_animal_classification():
    """Animal classification reasoning example."""
    print("\n" + "=" * 60)
    print("Example 3: Animal Classification")
    print("=" * 60)

    session = PykeSession("animals")

    # Add facts
    print("\nAdding facts about Rex (a dog):")
    facts = [
        "Animal(Rex, True)",
        "HasFur(Rex, True)",
        "Barks(Rex, True)",
        "HasTail(Rex, True)",
    ]
    for fact in facts:
        print(f"  {session.add_fact(fact)}")

    print("\nAdding facts about Tweety (a bird):")
    facts = [
        "Animal(Tweety, True)",
        "HasFeathers(Tweety, True)",
        "CanFly(Tweety, True)",
    ]
    for fact in facts:
        print(f"  {session.add_fact(fact)}")

    # Add classification rules
    print("\nAdding classification rules:")
    rules = [
        "Animal($x, True) && HasFur($x, True) >>> Mammal($x, True)",
        "Animal($x, True) && HasFeathers($x, True) >>> Bird($x, True)",
        "Mammal($x, True) && Barks($x, True) >>> Dog($x, True)",
        "Bird($x, True) && CanFly($x, True) >>> FlyingBird($x, True)",
    ]
    for rule in rules:
        print(f"  {session.add_rule(rule)}")

    # Queries
    print("\nQuery: Is Rex a dog?")
    result = session.query("Dog(Rex, True)")
    print(f"  Result: {result['result']}")
    print(f"  Explanation: {result['explanation']}")

    print("\nQuery: Is Rex a mammal?")
    result = session.query("Mammal(Rex, True)")
    print(f"  Result: {result['result']}")

    print("\nQuery: Is Tweety a bird?")
    result = session.query("Bird(Tweety, True)")
    print(f"  Result: {result['result']}")

    print("\nGoal: What mammals do we have?")
    result = session.prove("Mammal($animal, True)")
    print(f"  Bindings: {result['bindings']}")

    session.clear()


def example_load_program():
    """Example of loading a complete logic program."""
    print("\n" + "=" * 60)
    print("Example 4: Loading a Complete Program")
    print("=" * 60)

    session = PykeSession("loaded")

    program = """
Predicates:
Cold(x, bool)
Snowy(x, bool)
Winter(x, bool)
NorthernHemisphere(x, bool)

Facts:
NorthernHemisphere(Alaska, True)
NorthernHemisphere(Canada, True)
NorthernHemisphere(Norway, True)
Winter(December, True)
Winter(January, True)

Rules:
NorthernHemisphere($x, True) && Winter($month, True) >>> Cold($x, True)
Cold($x, True) >>> Snowy($x, True)

Query:
Snowy(Alaska, True)
"""

    print("\nLoading program...")
    print("-" * 40)
    print(program)
    print("-" * 40)

    # Parse and load the program manually
    session.clear()
    session.add_fact("NorthernHemisphere(Alaska, True)")
    session.add_fact("NorthernHemisphere(Canada, True)")
    session.add_fact("Winter(December, True)")
    session.add_rule("NorthernHemisphere($x, True) >>> Cold($x, True)")
    session.add_rule("Cold($x, True) >>> Snowy($x, True)")

    print("\nLoaded program:")
    print(session.get_program())

    print("\nQuery: Is Alaska snowy?")
    result = session.query("Snowy(Alaska, True)")
    print(f"  Result: {result['result']}")
    print(f"  Explanation: {result['explanation']}")

    session.clear()


def main():
    """Run all examples."""
    print("Pyke MCP Server - Usage Examples")
    print("=" * 60)

    try:
        from pyke import knowledge_engine
        print("\nPyke is installed. Running full examples...\n")

        example_classic_syllogism()
        example_family_relationships()
        example_animal_classification()
        example_load_program()

    except ImportError:
        print("\nWARNING: Pyke is not installed.")
        print("Install it with: pip install pyke3")
        print("\nRunning examples without query execution...\n")

        # Run examples that don't require Pyke engine
        session = PykeSession("demo")

        print("Adding facts and rules (no execution):")
        print(session.add_fact("Human(Socrates, True)"))
        print(session.add_rule("Human($x, True) >>> Mortal($x, True)"))
        print("\nProgram:")
        print(session.get_program())

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
