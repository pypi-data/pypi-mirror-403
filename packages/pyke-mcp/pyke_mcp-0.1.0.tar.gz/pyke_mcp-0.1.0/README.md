# Pyke MCP Server

An MCP (Model Context Protocol) server for the [Pyke](https://pyke.sourceforge.net/) logic programming inference engine. This server enables LLMs to perform logical reasoning through knowledge bases with facts, rules, and queries.

## Features

- **Fact Management**: Add ground truth facts to the knowledge base
- **Rule Definition**: Define inference rules using forward chaining
- **Query Execution**: Check if facts can be derived from the knowledge base
- **Goal Proving**: Find all variable bindings that satisfy a goal
- **Session Management**: Support multiple independent knowledge bases
- **Logic-LLM Compatible**: Load programs in Logic-LLM format

## Installation

### Using pip

```bash
pip install pyke-mcp
```

### From source

```bash
git clone https://github.com/yourusername/pyke-mcp.git
cd pyke-mcp
pip install -e .
```

### Dependencies

- Python 3.10+
- `mcp>=1.2.0`
- `pyke3>=1.1.1`

## Quick Start

### Running the Server

```bash
# Using the installed command
pyke-mcp

# Or using Python
python -m pyke_mcp.server
```

### Configuration for Claude Desktop

Add to your `claude_desktop_config.json`:

**macOS/Linux:**
```json
{
  "mcpServers": {
    "pyke": {
      "command": "pyke-mcp"
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "pyke": {
      "command": "pyke-mcp"
    }
  }
}
```

Or with explicit Python path:

```json
{
  "mcpServers": {
    "pyke": {
      "command": "python",
      "args": ["-m", "pyke_mcp.server"]
    }
  }
}
```

## Available Tools

### `add_fact`
Add a fact to the knowledge base.

```
Predicate(arg1, arg2, ...)
```

**Examples:**
- `Human(Socrates, True)` - Socrates is human
- `Parent(John, Mary)` - John is a parent of Mary

### `add_rule`
Add an inference rule using forward chaining.

```
Premise >>> Conclusion
Premise1 && Premise2 >>> Conclusion
```

**Examples:**
- `Human($x, True) >>> Mortal($x, True)` - All humans are mortal
- `Parent($x, $y) && Parent($y, $z) >>> Grandparent($x, $z)` - Grandparent relationship

### `add_facts_and_rules`
Bulk add multiple facts and rules at once.

### `query`
Check if a specific fact can be derived.

```
Predicate(Subject, ExpectedValue)
```

**Example:**
- `Mortal(Socrates, True)` - "Is Socrates mortal?"

### `prove_goal`
Find all variable bindings that satisfy a goal.

**Examples:**
- `Mortal($who, True)` - "Who is mortal?"
- `Parent($parent, Mary)` - "Who are Mary's parents?"

### `get_program`
Display the current knowledge base contents.

### `clear_program`
Clear all facts and rules from the session.

### `load_logic_program`
Load a complete logic program from formatted text (Logic-LLM compatible).

### `list_sessions`
List all active sessions.

### `delete_session`
Delete a specific session.

## Usage Examples

### Classic Syllogism

```
# Add facts
add_fact("Human(Socrates, True)")
add_fact("Human(Plato, True)")

# Add rule
add_rule("Human($x, True) >>> Mortal($x, True)")

# Query
query("Mortal(Socrates, True)")
# Result: True, Match: True

# Find all mortals
prove_goal("Mortal($who, True)")
# Bindings: who=Socrates, who=Plato
```

### Family Relationships

```
# Facts
add_fact("Parent(Alice, Bob)")
add_fact("Parent(Bob, Charlie)")
add_fact("Parent(Bob, Diana)")

# Rules
add_rule("Parent($x, $y) && Parent($y, $z) >>> Grandparent($x, $z)")

# Find Alice's grandchildren
prove_goal("Grandparent(Alice, $grandchild)")
# Bindings: grandchild=Charlie, grandchild=Diana
```

### Loading a Complete Program

```python
program = """
Predicates:
Human(x, bool)
Mortal(x, bool)

Facts:
Human(Socrates, True)
Human(Aristotle, True)

Rules:
Human($x, True) >>> Mortal($x, True)

Query:
Mortal(Socrates, True)
"""

load_logic_program(program)
```

## Logic Program Format

The server accepts programs in the Logic-LLM format:

```
Predicates:
PredicateName(arg1_type, arg2_type, ...)

Facts:
PredicateName(value1, value2, ...)

Rules:
Premise($var, value) >>> Conclusion($var, value)
Premise1($x, val) && Premise2($x, val) >>> Conclusion($x, val)

Query:
PredicateName(subject, expected_value)
```

### Syntax Rules

1. **Facts**: Ground assertions without variables
   - `Human(Socrates, True)`
   - `Age(John, 30)`

2. **Rules**: Implications with variables (prefixed with `$`)
   - `Human($x, True) >>> Mortal($x, True)`
   - Multiple premises joined with `&&`

3. **Variables**: Prefixed with `$`
   - `$x`, `$person`, `$value`

4. **Values**: Can be boolean (`True`/`False`) or strings
   - `True`, `False`, `Socrates`, `Blue`

## Session Management

The server supports multiple independent sessions:

```python
# Create/use a session
add_fact("Human(Socrates, True)", session_id="philosophy")

# Use a different session
add_fact("Cat(Whiskers, True)", session_id="animals")

# List sessions
list_sessions()

# Delete a session
delete_session("philosophy")
```

## Error Handling

The server provides clear error messages for:
- Invalid fact/rule syntax
- Query execution failures
- Missing Pyke installation
- Session not found

## Based On

- [Pyke Knowledge Engine](https://pyke.sourceforge.net/)
- [Logic-LLM](https://github.com/teacherpeterpan/Logic-LLM) - Pyke solver implementation
- [clingo-mcp](https://github.com/newjerseystyle/clingo-mcp) - MCP server interface reference

## License

MIT License
