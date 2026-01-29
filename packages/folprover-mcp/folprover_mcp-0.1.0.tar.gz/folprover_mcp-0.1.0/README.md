# FOL Prover MCP Server

An MCP (Model Context Protocol) server for First-Order Logic theorem proving using Vampire, E, and Prover9.

## Features

- **Multiple Provers**: Support for Vampire, E (eprover), Prover9, and built-in simple prover
- **Built-in Prover**: Simple resolution-based prover requires no external installation
- **FOL Parsing**: Parse and validate first-order logic formulas with Unicode notation
- **Session Management**: Build proofs incrementally with named sessions
- **TPTP Export**: Convert problems to standard TPTP format
- **Automatic Fallback**: Try multiple provers if one fails

## Installation

### Prerequisites

The server includes a **built-in simple prover** that works without any external installation. For more complex proofs, install one of the following theorem provers:

**Vampire** (recommended):
```bash
# Linux (Ubuntu/Debian)
sudo apt-get install vampire

# macOS (with Homebrew)
brew install vampire

# Or download from: https://github.com/vprover/vampire
```

**E Prover**:
```bash
# Linux (Ubuntu/Debian)
sudo apt-get install eprover

# macOS
brew install eprover

# Or download from: https://wwwlehre.dhbw-stuttgart.de/~sschulz/E/E.html
```

**Prover9**:
```bash
# Download from: https://www.cs.unm.edu/~mccune/prover9/
```

### Install the MCP Server

```bash
pip install folprover-mcp
```

Or install from source:
```bash
git clone https://github.com/folprover-mcp/folprover-mcp
cd folprover-mcp
pip install -e .
```

## Configuration

Add to your MCP client configuration:

### Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json` (Linux/macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "folprover": {
      "command": "folprover-mcp"
    }
  }
}
```

### VS Code with Continue

Add to your Continue configuration:

```json
{
  "mcpServers": {
    "folprover": {
      "command": "folprover-mcp"
    }
  }
}
```

## Usage

### FOL Notation

The server supports standard FOL notation with Unicode operators:

| Symbol | Meaning | Example |
|--------|---------|---------|
| `∀` | Universal quantifier | `∀x P(x)` |
| `∃` | Existential quantifier | `∃x P(x)` |
| `∧` | Conjunction (AND) | `P(x) ∧ Q(x)` |
| `∨` | Disjunction (OR) | `P(x) ∨ Q(x)` |
| `→` | Implication | `P(x) → Q(x)` |
| `↔` | Biconditional | `P(x) ↔ Q(x)` |
| `¬` | Negation | `¬P(x)` |
| `⊕` | Exclusive OR | `P(x) ⊕ Q(x)` |

You can also use ASCII alternatives:
- `forall` or `all` for `∀`
- `exists` for `∃`
- `&` or `and` for `∧`
- `|` or `or` for `∨`
- `->` or `implies` for `→`
- `<->` or `iff` for `↔`
- `~` or `not` for `¬`

### Tools

#### `prove`
Execute a FOL proof directly:

```json
{
  "premises": [
    "∀x (Human(x) → Mortal(x))",
    "Human(socrates)"
  ],
  "conclusion": "Mortal(socrates)",
  "prover": "vampire"
}
```

#### `add_premise`
Add a premise to the current session:

```json
{
  "premise": "∀x (Human(x) → Mortal(x))"
}
```

#### `set_conclusion`
Set the conclusion to prove:

```json
{
  "conclusion": "Mortal(socrates)"
}
```

#### `prove_session`
Prove using the current session's premises and conclusion:

```json
{
  "prover": "vampire"
}
```

#### `parse_formula`
Parse and validate a FOL formula:

```json
{
  "formula": "∀x (P(x) → Q(x))"
}
```

#### `convert_to_tptp`
Convert a problem to TPTP format:

```json
{
  "premises": ["∀x (P(x) → Q(x))", "P(a)"],
  "conclusion": "Q(a)"
}
```

#### `list_provers`
List available theorem provers:

```json
{}
```

### Session Management

- `create_session`: Create a new named session
- `list_sessions`: List all active sessions
- `switch_session`: Switch to a different session
- `get_session`: Get current session state
- `clear_session`: Clear all premises and conclusion
- `remove_premise`: Remove a premise by index

## Examples

### Example 1: Classic Syllogism

**Premises:**
1. All humans are mortal: `∀x (Human(x) → Mortal(x))`
2. Socrates is human: `Human(socrates)`

**Conclusion:** Socrates is mortal: `Mortal(socrates)`

**Result:** Theorem (True)

### Example 2: Set Theory

**Premises:**
1. If x is a subset of y and y is a subset of z, then x is a subset of z:
   `∀x ∀y ∀z ((Subset(x,y) ∧ Subset(y,z)) → Subset(x,z))`
2. A is a subset of B: `Subset(a, b)`
3. B is a subset of C: `Subset(b, c)`

**Conclusion:** A is a subset of C: `Subset(a, c)`

**Result:** Theorem (True)

### Example 3: With Counter-model

**Premises:**
1. Some birds can fly: `∃x (Bird(x) ∧ CanFly(x))`

**Conclusion:** All birds can fly: `∀x (Bird(x) → CanFly(x))`

**Result:** Not a theorem (False - there's a counter-model where some bird can't fly)

## Architecture

```
folprover-mcp/
├── src/folprover_mcp/
│   ├── __init__.py
│   ├── server.py          # MCP server implementation
│   ├── provers.py         # Prover interfaces (Vampire, E, Prover9, Simple)
│   ├── simple_prover.py   # Built-in resolution prover
│   ├── fol_parser.py      # FOL formula parser
│   └── tptp_converter.py  # TPTP format converter
├── tests/                 # Test suite
├── examples/              # Example proof problems
├── pyproject.toml
└── README.md
```

## References

- [Vampire Theorem Prover](https://github.com/vprover/vampire)
- [E Theorem Prover](https://wwwlehre.dhbw-stuttgart.de/~sschulz/E/E.html)
- [Prover9](https://www.cs.unm.edu/~mccune/prover9/)
- [TPTP Problem Library](https://www.tptp.org/)
- [Logic-LLM](https://github.com/teacherpeterpan/Logic-LLM) - Original inspiration
- [MCP Specification](https://modelcontextprotocol.io/)

## License

MIT License
