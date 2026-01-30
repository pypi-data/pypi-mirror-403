"""
Ollama integration for prmpt.

Provides an enforced LLM client that applies .prmpt contracts
to Ollama interactions.

Example:
    >>> from prmpt import load
    >>> from prmpt.integrations import OllamaEnforcer
    >>>
    >>> contract = load("my-bot.prmpt")
    >>> enforcer = OllamaEnforcer(contract, model="llama3")
    >>> result = enforcer.execute({"user_query": "Hello", "user_id": "123"})
"""

import json
import subprocess
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from ..contract import Contract
from ..exceptions import HandoffRequired


class OllamaClient:
    """Simple client for Ollama API."""

    def __init__(self, model: str = "llama3:latest", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama client.

        Args:
            model: Ollama model name
            base_url: Ollama API base URL
        """
        self.model = model
        self.base_url = base_url
        self._check_ollama()

    def _check_ollama(self):
        """Check if Ollama is running."""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Ollama is not running. Start with: ollama serve")
        except FileNotFoundError:
            raise RuntimeError("Ollama not found. Install from: https://ollama.ai/download")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Ollama did not respond.")

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        format: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate completion using Ollama.

        Args:
            prompt: User prompt
            system: System prompt
            format: Output format ('json' for JSON mode)
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        payload = {
            'model': self.model,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': temperature}
        }

        if system:
            payload['system'] = system

        if format == 'json':
            payload['format'] = 'json'

        try:
            req = urllib.request.Request(
                f'{self.base_url}/api/generate',
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=120) as response:
                response_text = response.read().decode('utf-8')
                full_response = ''
                for line in response_text.strip().split('\n'):
                    if line:
                        try:
                            chunk = json.loads(line)
                            if 'response' in chunk:
                                full_response += chunk['response']
                            if chunk.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
                return full_response

        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to connect to Ollama: {e}")
        except Exception as e:
            raise RuntimeError(f"Ollama request failed: {e}")


class ExecutionResult:
    """Result of an enforced LLM execution."""

    def __init__(
        self,
        success: bool,
        output: Optional[str] = None,
        parsed_output: Optional[Any] = None,
        violations: Optional[List[str]] = None,
        failure_mode: Optional[Dict[str, Any]] = None,
        handoff: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.output = output
        self.parsed_output = parsed_output
        self.violations = violations or []
        self.failure_mode = failure_mode
        self.handoff = handoff
        self.metadata = metadata or {}

    def __repr__(self):
        return f"ExecutionResult(success={self.success}, violations={self.violations})"


class OllamaEnforcer:
    """
    Enforced Ollama client with .prmpt contract enforcement.

    Validates inputs, generates system prompts, validates outputs,
    and handles failures according to the contract.

    Example:
        >>> contract = prmpt.load("my-bot.prmpt")
        >>> enforcer = OllamaEnforcer(contract)
        >>> result = enforcer.execute({"user_query": "Hello", "user_id": "123"})
        >>> if result.success:
        ...     print(result.output)
    """

    def __init__(
        self,
        contract: Contract,
        model: str = "llama3:latest",
        base_url: str = "http://localhost:11434",
    ):
        """
        Initialize enforced client.

        Args:
            contract: prmpt Contract instance
            model: Ollama model name
            base_url: Ollama API base URL
        """
        self.contract = contract
        self.ollama = OllamaClient(model, base_url)
        self.execution_log: List[Dict[str, Any]] = []

    def execute(
        self,
        user_input: Dict[str, Any],
        temperature: Optional[float] = None,
    ) -> ExecutionResult:
        """
        Execute an LLM interaction with full contract enforcement.

        Args:
            user_input: User input parameters
            temperature: Override temperature

        Returns:
            ExecutionResult with success status, output, and metadata
        """
        # Step 1: Validate input
        input_errors = self.contract.validate_input(user_input)
        if input_errors:
            result = ExecutionResult(
                success=False,
                violations=input_errors,
                failure_mode=self.contract.handle_failure('invalid_input'),
            )
            self._log(user_input, None, input_errors)
            return result

        # Step 2: Check handoff
        if self.contract.should_handoff(user_input):
            result = ExecutionResult(
                success=False,
                handoff=True,
                failure_mode=self.contract.handle_failure('out_of_scope'),
            )
            self._log(user_input, None, ['Handoff required'])
            return result

        # Step 3: Generate system prompt
        system_prompt = self.contract.to_system_prompt()

        # Step 4: Get temperature
        if temperature is None:
            temperature = self.contract.parameters.get('temperature', 0.7)

        # Step 5: Determine output format
        output_format = None
        if self.contract.outputs.get('format') in ['json', 'structured']:
            output_format = 'json'

        # Step 6: Call LLM
        user_query = user_input.get('user_query', user_input.get('query', ''))

        try:
            llm_output = self.ollama.generate(
                prompt=user_query,
                system=system_prompt,
                format=output_format,
                temperature=temperature,
            )
        except Exception as e:
            result = ExecutionResult(
                success=False,
                violations=[f"LLM error: {str(e)}"],
                failure_mode=self.contract.handle_failure('timeout'),
            )
            self._log(user_input, None, [str(e)])
            return result

        # Step 7: Validate output
        output_errors = self.contract.validate_output(llm_output)
        if output_errors:
            result = ExecutionResult(
                success=False,
                output=llm_output,
                violations=output_errors,
                failure_mode=self.contract.handle_failure('invalid_output'),
            )
            self._log(user_input, llm_output, output_errors)
            return result

        # Success!
        parsed = None
        if output_format == 'json':
            try:
                parsed = json.loads(llm_output)
            except json.JSONDecodeError:
                pass

        result = ExecutionResult(
            success=True,
            output=llm_output,
            parsed_output=parsed,
            metadata={'model': self.ollama.model, 'temperature': temperature},
        )
        self._log(user_input, llm_output, [])
        return result

    def _log(
        self,
        user_input: Dict[str, Any],
        output: Optional[str],
        violations: List[str],
    ):
        """Add entry to execution log."""
        self.execution_log.append({
            'contract': {
                'name': self.contract.name,
                'version': self.contract.version,
            },
            'input': user_input,
            'output': output,
            'violations': violations,
        })

    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get the full execution log for audit."""
        return self.execution_log
