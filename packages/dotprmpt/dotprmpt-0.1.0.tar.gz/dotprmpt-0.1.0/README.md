# prmpt

**System-enforced LLM contracts.**

> **prmpt does NOT make LLMs obedient.** LLMs will still hallucinate, ignore instructions, and produce invalid output. prmpt makes **violations observable** and **system behavior deterministic**.

```
Traditional:  "Please follow rules" → LLM → Hope it works
   prmpt:     Validate input → LLM → Catch violations → Handle failure
```

The LLM is an untrusted black box. Your system decides what to do when it misbehaves.

## Install

```bash
pip install dotprmpt
```

## Quick Start

```python
import prmpt

# Load a contract
contract = prmpt.load("my-bot.prmpt")

# Validate input
errors = contract.validate_input({"query": "Hello", "user_id": "123"})

# Generate system prompt
system_prompt = contract.to_system_prompt()

# After LLM response, validate output
errors = contract.validate_output(llm_response)
```

## With Ollama

```python
import prmpt
from prmpt.integrations import OllamaEnforcer

contract = prmpt.load("my-bot.prmpt")
enforcer = OllamaEnforcer(contract, model="llama3")

result = enforcer.execute({
    "user_query": "How do I reset my password?",
    "user_id": "user-123"
})

if result.success:
    print(result.output)
else:
    print(f"Violations: {result.violations}")
```

## Demo

```bash
# Requires Ollama: https://ollama.ai/download
make demo
```

## The Contract

A `.prmpt` file defines what the LLM can and cannot do:

```yaml
Identity:
  name: "support-bot"
  version: "1.0.0"
  spec_version: "0.1.0"

Scope:
  description: "Customer support assistant"
  boundaries:
    - "Only answer product questions"

Invariants:
  - "Always be polite"
  - "Never share internal details"

Allowed Actions:
  - "answer questions"
  - "search knowledge base"

Forbidden Actions:
  - "access payment info"
  - "modify accounts"

Inputs:
  parameters:
    user_query: {type: "string", required: true}
    user_id: {type: "string", required: true}

Outputs:
  format: "json"
  schema:
    type: "object"
    properties:
      answer: {type: "string"}

Validation:
  mode: "schema"

Failure Modes:
  - id: "invalid_input"
    action: "return error"
  - id: "out_of_scope"
    action: "handoff to human"

Handoff Rules:
  conditions:
    - "user requests human"
```

## CLI

```bash
prmpt validate contract.prmpt   # Validate structure
prmpt info contract.prmpt       # Show contract info
prmpt prompt contract.prmpt     # Generate system prompt
prmpt resolve contract.prmpt    # Output canonical JSON
```

## API

```python
import prmpt

# Load
contract = prmpt.load("file.prmpt")
contract = prmpt.loads(yaml_string)

# Validate files
errors = prmpt.validate("file.prmpt")           # Returns list
prmpt.validate("file.prmpt", strict=True)       # Raises on error

# Contract properties
contract.name                 # "support-bot"
contract.version              # "1.0.0"
contract.spec_version         # "0.1.0"
contract.invariants           # List[str]
contract.allowed_actions      # Set[str]
contract.forbidden_actions    # Set[str]

# Contract methods
contract.to_system_prompt()           # Generate LLM instructions
contract.validate_input(data)         # Validate input → List[str]
contract.validate_output(text)        # Validate output → List[str]
contract.check_action("do_thing")     # Is action allowed? → bool
contract.should_handoff(data)         # Should handoff? → bool

# Exceptions
from prmpt import (
    ParseError,         # Bad YAML/JSON
    ValidationError,    # Invalid contract
    InputViolation,     # Bad input
    OutputViolation,    # Bad output
    ActionForbidden,    # Action not allowed
    HandoffRequired,    # Needs human
)
```

## Versioning

```python
import prmpt
prmpt.__version__       # "0.1.0" - library version
prmpt.__spec_version__  # "0.1.0" - spec version
```

## Project Structure

```
src/prmpt/       # Python package
spec/            # Specification document
tests/           # Test contracts
examples/        # Usage examples
```

## Status

**Experimental (v0.1.0)** — Breaking changes expected.

## License

Apache 2.0
