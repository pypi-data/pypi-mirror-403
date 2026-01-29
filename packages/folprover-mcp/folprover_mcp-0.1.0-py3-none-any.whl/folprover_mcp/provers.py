"""
FOL Prover Interface

Supports:
- Vampire: High-performance theorem prover
- E (eprover): Equational theorem prover
- Prover9: Legacy theorem prover

Each prover returns a result with status (Theorem, Unsatisfiable, Timeout, Unknown, Error)
"""

import os
import shutil
import subprocess
import tempfile
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from .tptp_converter import TPTPConverter, Prover9Converter
from .simple_prover import SimpleResolutionProver, SimpleProofResult


class ProofResult(Enum):
    """Possible results from a theorem prover."""
    THEOREM = "Theorem"           # Conjecture proven (follows from axioms)
    UNSATISFIABLE = "Unsatisfiable"  # Negation leads to contradiction
    SATISFIABLE = "Satisfiable"   # Formula is satisfiable (not a theorem)
    TIMEOUT = "Timeout"           # Prover timed out
    UNKNOWN = "Unknown"           # Could not determine
    ERROR = "Error"               # Error occurred


@dataclass
class ProverOutput:
    """Output from a theorem prover."""
    result: ProofResult
    answer: str  # 'True', 'False', 'Unknown'
    raw_output: str
    proof: Optional[str] = None
    error_message: Optional[str] = None
    time_taken: Optional[float] = None


class BaseProver(ABC):
    """Abstract base class for theorem provers."""

    def __init__(self, timeout: int = 30):
        """
        Initialize prover.

        Args:
            timeout: Maximum time in seconds for proof attempt
        """
        self.timeout = timeout

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the prover is installed and available."""
        pass

    @abstractmethod
    def prove(
        self,
        premises: List[str],
        conclusion: str
    ) -> ProverOutput:
        """
        Attempt to prove a conclusion from premises.

        Args:
            premises: List of premise formulas
            conclusion: Conclusion to prove

        Returns:
            ProverOutput with result and details
        """
        pass

    def _run_command(self, cmd: List[str], input_file: str) -> Tuple[str, str, int]:
        """Run a command and return stdout, stderr, return code."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Timeout", -1
        except Exception as e:
            return "", str(e), -2


class VampireProver(BaseProver):
    """Interface to the Vampire theorem prover."""

    def __init__(self, timeout: int = 30, vampire_path: Optional[str] = None):
        super().__init__(timeout)
        self.vampire_path = vampire_path or self._find_vampire()
        self.converter = TPTPConverter()

    def _find_vampire(self) -> str:
        """Find Vampire executable in PATH."""
        # Try common names
        for name in ['vampire', 'vampire_z3', 'vampire.exe']:
            path = shutil.which(name)
            if path:
                return path
        return 'vampire'  # Default, may not exist

    def is_available(self) -> bool:
        """Check if Vampire is installed."""
        try:
            result = subprocess.run(
                [self.vampire_path, '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0 or 'Vampire' in result.stdout.decode()
        except Exception:
            return False

    def prove(
        self,
        premises: List[str],
        conclusion: str
    ) -> ProverOutput:
        """
        Prove using Vampire.

        Vampire uses refutation: proves by showing the negation leads to contradiction.
        """
        # Create TPTP problem file
        problem = self.converter.create_problem(premises, conclusion)

        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.p',
            delete=False
        ) as f:
            f.write(problem)
            problem_file = f.name

        try:
            # Run Vampire
            cmd = [
                self.vampire_path,
                '--mode', 'casc',
                '--time_limit', str(self.timeout),
                problem_file
            ]

            stdout, stderr, returncode = self._run_command(cmd, problem_file)

            if returncode == -1:
                return ProverOutput(
                    result=ProofResult.TIMEOUT,
                    answer="Unknown",
                    raw_output=stdout + stderr
                )

            # Parse Vampire output
            return self._parse_output(stdout + stderr)

        finally:
            os.unlink(problem_file)

    def _parse_output(self, output: str) -> ProverOutput:
        """Parse Vampire output to determine result."""
        # Check for theorem (refutation found)
        if 'Refutation found' in output or 'Theorem' in output:
            # Extract proof if present
            proof = self._extract_proof(output)
            return ProverOutput(
                result=ProofResult.THEOREM,
                answer="True",
                raw_output=output,
                proof=proof
            )

        # Check for satisfiable (counter-model found)
        if 'Satisfiable' in output or 'CounterSatisfiable' in output:
            return ProverOutput(
                result=ProofResult.SATISFIABLE,
                answer="False",
                raw_output=output
            )

        # Check for timeout
        if 'Time limit reached' in output or 'timeout' in output.lower():
            return ProverOutput(
                result=ProofResult.TIMEOUT,
                answer="Unknown",
                raw_output=output
            )

        # Unknown result
        return ProverOutput(
            result=ProofResult.UNKNOWN,
            answer="Unknown",
            raw_output=output
        )

    def _extract_proof(self, output: str) -> Optional[str]:
        """Extract proof from Vampire output."""
        lines = output.split('\n')
        proof_lines = []
        in_proof = False

        for line in lines:
            if 'Refutation found' in line:
                in_proof = True
            if in_proof:
                proof_lines.append(line)
            if in_proof and line.strip() == '':
                break

        return '\n'.join(proof_lines) if proof_lines else None


class EProver(BaseProver):
    """Interface to the E theorem prover."""

    def __init__(self, timeout: int = 30, eprover_path: Optional[str] = None):
        super().__init__(timeout)
        self.eprover_path = eprover_path or self._find_eprover()
        self.converter = TPTPConverter()

    def _find_eprover(self) -> str:
        """Find E prover executable in PATH."""
        for name in ['eprover', 'eprover.exe', 'E']:
            path = shutil.which(name)
            if path:
                return path
        return 'eprover'

    def is_available(self) -> bool:
        """Check if E prover is installed."""
        try:
            result = subprocess.run(
                [self.eprover_path, '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0 or 'E ' in result.stdout.decode()
        except Exception:
            return False

    def prove(
        self,
        premises: List[str],
        conclusion: str
    ) -> ProverOutput:
        """Prove using E prover."""
        problem = self.converter.create_problem(premises, conclusion)

        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.p',
            delete=False
        ) as f:
            f.write(problem)
            problem_file = f.name

        try:
            cmd = [
                self.eprover_path,
                '--auto',
                '--tptp3-format',
                '--silent',
                f'--cpu-limit={self.timeout}',
                problem_file
            ]

            stdout, stderr, returncode = self._run_command(cmd, problem_file)

            if returncode == -1:
                return ProverOutput(
                    result=ProofResult.TIMEOUT,
                    answer="Unknown",
                    raw_output=stdout + stderr
                )

            return self._parse_output(stdout + stderr, returncode)

        finally:
            os.unlink(problem_file)

    def _parse_output(self, output: str, returncode: int) -> ProverOutput:
        """Parse E prover output."""
        # E uses SZS status indicators
        if 'SZS status Theorem' in output or 'SZS status Unsatisfiable' in output:
            return ProverOutput(
                result=ProofResult.THEOREM,
                answer="True",
                raw_output=output
            )

        if 'SZS status CounterSatisfiable' in output or 'SZS status Satisfiable' in output:
            return ProverOutput(
                result=ProofResult.SATISFIABLE,
                answer="False",
                raw_output=output
            )

        if 'SZS status Timeout' in output or 'SZS status ResourceOut' in output:
            return ProverOutput(
                result=ProofResult.TIMEOUT,
                answer="Unknown",
                raw_output=output
            )

        # Check return code
        if returncode == 0:
            return ProverOutput(
                result=ProofResult.THEOREM,
                answer="True",
                raw_output=output
            )

        return ProverOutput(
            result=ProofResult.UNKNOWN,
            answer="Unknown",
            raw_output=output
        )


class Prover9Prover(BaseProver):
    """Interface to Prover9 theorem prover."""

    def __init__(self, timeout: int = 30, prover9_path: Optional[str] = None):
        super().__init__(timeout)
        self.prover9_path = prover9_path or self._find_prover9()
        self.converter = Prover9Converter()

    def _find_prover9(self) -> str:
        """Find Prover9 executable."""
        for name in ['prover9', 'prover9.exe']:
            path = shutil.which(name)
            if path:
                return path
        return 'prover9'

    def is_available(self) -> bool:
        """Check if Prover9 is installed."""
        try:
            result = subprocess.run(
                [self.prover9_path, '--version'],
                capture_output=True,
                timeout=5
            )
            return 'Prover9' in result.stdout.decode() or 'LADR' in result.stdout.decode()
        except Exception:
            return False

    def prove(
        self,
        premises: List[str],
        conclusion: str
    ) -> ProverOutput:
        """Prove using Prover9."""
        problem = self.converter.create_problem(premises, conclusion)

        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.in',
            delete=False
        ) as f:
            # Add timeout setting
            f.write(f"assign(max_seconds, {self.timeout}).\n\n")
            f.write(problem)
            problem_file = f.name

        try:
            cmd = [self.prover9_path, '-f', problem_file]

            stdout, stderr, returncode = self._run_command(cmd, problem_file)

            if returncode == -1:
                return ProverOutput(
                    result=ProofResult.TIMEOUT,
                    answer="Unknown",
                    raw_output=stdout + stderr
                )

            return self._parse_output(stdout + stderr, returncode)

        finally:
            os.unlink(problem_file)

    def _parse_output(self, output: str, returncode: int) -> ProverOutput:
        """Parse Prover9 output."""
        if 'THEOREM PROVED' in output or returncode == 0:
            return ProverOutput(
                result=ProofResult.THEOREM,
                answer="True",
                raw_output=output
            )

        if 'SEARCH FAILED' in output:
            return ProverOutput(
                result=ProofResult.UNKNOWN,
                answer="Unknown",
                raw_output=output
            )

        if 'MAX_SECONDS' in output or 'max_seconds' in output.lower():
            return ProverOutput(
                result=ProofResult.TIMEOUT,
                answer="Unknown",
                raw_output=output
            )

        return ProverOutput(
            result=ProofResult.UNKNOWN,
            answer="Unknown",
            raw_output=output
        )


class SimpleProver(BaseProver):
    """Built-in simple resolution prover (no external dependencies)."""

    def __init__(self, timeout: int = 30):
        super().__init__(timeout)
        self.prover = SimpleResolutionProver(max_iterations=1000)

    def is_available(self) -> bool:
        """Always available as it's built-in."""
        return True

    def prove(
        self,
        premises: List[str],
        conclusion: str
    ) -> ProverOutput:
        """Prove using simple resolution."""
        try:
            result, steps = self.prover.prove(premises, conclusion)

            if result == SimpleProofResult.THEOREM:
                return ProverOutput(
                    result=ProofResult.THEOREM,
                    answer="True",
                    raw_output="\n".join(steps),
                    proof="\n".join(steps)
                )
            elif result == SimpleProofResult.NOT_THEOREM:
                return ProverOutput(
                    result=ProofResult.SATISFIABLE,
                    answer="False",
                    raw_output="\n".join(steps)
                )
            else:
                return ProverOutput(
                    result=ProofResult.UNKNOWN,
                    answer="Unknown",
                    raw_output="\n".join(steps)
                )
        except Exception as e:
            return ProverOutput(
                result=ProofResult.ERROR,
                answer="Unknown",
                raw_output="",
                error_message=str(e)
            )


class FOLProverManager:
    """Manages multiple FOL provers and provides unified interface."""

    PROVERS = {
        'vampire': VampireProver,
        'eprover': EProver,
        'prover9': Prover9Prover,
        'simple': SimpleProver,
    }

    def __init__(self, default_timeout: int = 30):
        self.timeout = default_timeout
        self._provers = {}

    def get_prover(self, name: str) -> BaseProver:
        """Get a prover instance by name."""
        name = name.lower()
        if name not in self.PROVERS:
            raise ValueError(f"Unknown prover: {name}. Available: {list(self.PROVERS.keys())}")

        if name not in self._provers:
            self._provers[name] = self.PROVERS[name](timeout=self.timeout)

        return self._provers[name]

    def list_available_provers(self) -> List[dict]:
        """List all provers and their availability status."""
        result = []
        for name, prover_class in self.PROVERS.items():
            prover = prover_class(timeout=5)
            result.append({
                'name': name,
                'available': prover.is_available(),
                'description': prover_class.__doc__.strip().split('\n')[0] if prover_class.__doc__ else ''
            })
        return result

    def prove(
        self,
        premises: List[str],
        conclusion: str,
        prover_name: str = 'vampire'
    ) -> ProverOutput:
        """
        Prove a conclusion from premises using specified prover.

        Args:
            premises: List of premise formulas
            conclusion: Conclusion to prove
            prover_name: Name of prover to use

        Returns:
            ProverOutput with result
        """
        prover = self.get_prover(prover_name)

        if not prover.is_available():
            return ProverOutput(
                result=ProofResult.ERROR,
                answer="Unknown",
                raw_output="",
                error_message=f"Prover '{prover_name}' is not available. Please install it."
            )

        return prover.prove(premises, conclusion)

    def prove_with_fallback(
        self,
        premises: List[str],
        conclusion: str,
        preferred_provers: Optional[List[str]] = None
    ) -> Tuple[ProverOutput, str]:
        """
        Try provers in order until one succeeds.

        Args:
            premises: List of premise formulas
            conclusion: Conclusion to prove
            preferred_provers: Order of provers to try

        Returns:
            Tuple of (ProverOutput, prover_name_used)
        """
        if preferred_provers is None:
            preferred_provers = ['vampire', 'eprover', 'prover9']

        for prover_name in preferred_provers:
            try:
                prover = self.get_prover(prover_name)
                if prover.is_available():
                    result = prover.prove(premises, conclusion)
                    if result.result not in [ProofResult.ERROR, ProofResult.TIMEOUT]:
                        return result, prover_name
            except Exception:
                continue

        # All failed, return last result or error
        return ProverOutput(
            result=ProofResult.ERROR,
            answer="Unknown",
            raw_output="",
            error_message="No prover available or all provers failed."
        ), "none"
