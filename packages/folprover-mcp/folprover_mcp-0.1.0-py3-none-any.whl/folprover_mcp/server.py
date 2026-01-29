"""
FOL Prover MCP Server

An MCP server for First-Order Logic theorem proving using Vampire, E, and Prover9.

Features:
- Parse and validate FOL formulas
- Build proof problems incrementally
- Execute proofs with multiple provers
- Session management for complex proofs
"""

import json
import logging
from typing import Any, Optional, List, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    EmbeddedResource,
    INTERNAL_ERROR,
    INVALID_PARAMS,
)

from .provers import FOLProverManager, ProofResult
from .tptp_converter import TPTPConverter
from .fol_parser import FOLFormula

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("folprover-mcp")


class FOLSession:
    """Manages a FOL proving session with premises and conclusions."""

    def __init__(self):
        self.premises: List[str] = []
        self.conclusion: Optional[str] = None
        self.name: str = "default"

    def add_premise(self, premise: str) -> int:
        """Add a premise and return its index."""
        self.premises.append(premise)
        return len(self.premises) - 1

    def remove_premise(self, index: int) -> bool:
        """Remove a premise by index."""
        if 0 <= index < len(self.premises):
            self.premises.pop(index)
            return True
        return False

    def set_conclusion(self, conclusion: str):
        """Set the conclusion to prove."""
        self.conclusion = conclusion

    def clear(self):
        """Clear all premises and conclusion."""
        self.premises = []
        self.conclusion = None

    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "name": self.name,
            "premises": self.premises,
            "conclusion": self.conclusion,
            "premise_count": len(self.premises),
            "ready_to_prove": self.conclusion is not None and len(self.premises) > 0
        }


class FOLProverMCPServer:
    """MCP Server for FOL theorem proving."""

    def __init__(self):
        self.server = Server("folprover-mcp")
        self.prover_manager = FOLProverManager(default_timeout=30)
        self.converter = TPTPConverter()
        self.sessions: Dict[str, FOLSession] = {"default": FOLSession()}
        self.current_session = "default"

        self._setup_tools()

    def _setup_tools(self):
        """Register all MCP tools."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="prove",
                    description="Execute a FOL proof. Attempts to prove the conclusion from the given premises using the specified theorem prover (vampire, eprover, or prover9).",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "premises": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of premise formulas in FOL notation. Supports Unicode operators: ∀ (forall), ∃ (exists), ∧ (and), ∨ (or), → (implies), ↔ (iff), ¬ (not)"
                            },
                            "conclusion": {
                                "type": "string",
                                "description": "The conclusion to prove from the premises"
                            },
                            "prover": {
                                "type": "string",
                                "enum": ["vampire", "eprover", "prover9", "simple"],
                                "default": "vampire",
                                "description": "Which theorem prover to use (simple is built-in, others require installation)"
                            },
                            "timeout": {
                                "type": "integer",
                                "default": 30,
                                "description": "Timeout in seconds for the proof attempt"
                            }
                        },
                        "required": ["premises", "conclusion"]
                    }
                ),
                Tool(
                    name="prove_session",
                    description="Execute a proof using the current session's premises and conclusion.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prover": {
                                "type": "string",
                                "enum": ["vampire", "eprover", "prover9", "simple"],
                                "default": "vampire",
                                "description": "Which theorem prover to use (simple is built-in, others require installation)"
                            },
                            "session": {
                                "type": "string",
                                "description": "Session name (defaults to current session)"
                            }
                        }
                    }
                ),
                Tool(
                    name="add_premise",
                    description="Add a premise (axiom) to the current session for incremental proof building.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "premise": {
                                "type": "string",
                                "description": "FOL formula to add as a premise"
                            },
                            "session": {
                                "type": "string",
                                "description": "Session name (defaults to current session)"
                            }
                        },
                        "required": ["premise"]
                    }
                ),
                Tool(
                    name="set_conclusion",
                    description="Set the conclusion (goal) to prove in the current session.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "conclusion": {
                                "type": "string",
                                "description": "FOL formula to prove"
                            },
                            "session": {
                                "type": "string",
                                "description": "Session name (defaults to current session)"
                            }
                        },
                        "required": ["conclusion"]
                    }
                ),
                Tool(
                    name="clear_session",
                    description="Clear all premises and conclusion from a session.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session": {
                                "type": "string",
                                "description": "Session name to clear (defaults to current session)"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_session",
                    description="Get the current state of a session including all premises and conclusion.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session": {
                                "type": "string",
                                "description": "Session name (defaults to current session)"
                            }
                        }
                    }
                ),
                Tool(
                    name="parse_formula",
                    description="Parse and validate a FOL formula. Returns information about variables, constants, predicates, and whether the formula is syntactically valid.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "formula": {
                                "type": "string",
                                "description": "FOL formula to parse"
                            }
                        },
                        "required": ["formula"]
                    }
                ),
                Tool(
                    name="convert_to_tptp",
                    description="Convert a FOL problem to TPTP format (standard format for theorem provers).",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "premises": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of premise formulas"
                            },
                            "conclusion": {
                                "type": "string",
                                "description": "Conclusion formula"
                            }
                        },
                        "required": ["premises", "conclusion"]
                    }
                ),
                Tool(
                    name="list_provers",
                    description="List available theorem provers and their status.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="create_session",
                    description="Create a new named session for proof building.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name for the new session"
                            }
                        },
                        "required": ["name"]
                    }
                ),
                Tool(
                    name="list_sessions",
                    description="List all active sessions.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="switch_session",
                    description="Switch to a different session.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Session name to switch to"
                            }
                        },
                        "required": ["name"]
                    }
                ),
                Tool(
                    name="remove_premise",
                    description="Remove a premise by index from the current session.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "index": {
                                "type": "integer",
                                "description": "Index of the premise to remove (0-based)"
                            },
                            "session": {
                                "type": "string",
                                "description": "Session name (defaults to current session)"
                            }
                        },
                        "required": ["index"]
                    }
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            try:
                result = await self._handle_tool(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in tool {name}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)})
                )]

    def _get_session(self, name: Optional[str] = None) -> FOLSession:
        """Get a session by name or the current session."""
        session_name = name or self.current_session
        if session_name not in self.sessions:
            raise ValueError(f"Session '{session_name}' not found")
        return self.sessions[session_name]

    async def _handle_tool(self, name: str, arguments: dict) -> dict:
        """Handle tool calls."""

        if name == "prove":
            premises = arguments.get("premises", [])
            conclusion = arguments.get("conclusion", "")
            prover = arguments.get("prover", "vampire")
            timeout = arguments.get("timeout", 30)

            if not premises:
                return {"error": "At least one premise is required"}
            if not conclusion:
                return {"error": "Conclusion is required"}

            # Set timeout
            self.prover_manager.timeout = timeout

            # Execute proof
            result = self.prover_manager.prove(premises, conclusion, prover)

            return {
                "result": result.result.value,
                "answer": result.answer,
                "prover": prover,
                "proof": result.proof,
                "error": result.error_message,
                "raw_output": result.raw_output[:2000] if result.raw_output else None
            }

        elif name == "prove_session":
            session = self._get_session(arguments.get("session"))
            prover = arguments.get("prover", "vampire")

            if not session.premises:
                return {"error": "No premises in session. Use add_premise first."}
            if not session.conclusion:
                return {"error": "No conclusion set. Use set_conclusion first."}

            result = self.prover_manager.prove(
                session.premises,
                session.conclusion,
                prover
            )

            return {
                "result": result.result.value,
                "answer": result.answer,
                "prover": prover,
                "premises_used": len(session.premises),
                "conclusion": session.conclusion,
                "proof": result.proof,
                "error": result.error_message
            }

        elif name == "add_premise":
            session = self._get_session(arguments.get("session"))
            premise = arguments.get("premise", "")

            if not premise:
                return {"error": "Premise cannot be empty"}

            index = session.add_premise(premise)
            return {
                "success": True,
                "index": index,
                "premise": premise,
                "total_premises": len(session.premises)
            }

        elif name == "set_conclusion":
            session = self._get_session(arguments.get("session"))
            conclusion = arguments.get("conclusion", "")

            if not conclusion:
                return {"error": "Conclusion cannot be empty"}

            session.set_conclusion(conclusion)
            return {
                "success": True,
                "conclusion": conclusion,
                "ready_to_prove": len(session.premises) > 0
            }

        elif name == "clear_session":
            session = self._get_session(arguments.get("session"))
            session.clear()
            return {"success": True, "message": "Session cleared"}

        elif name == "get_session":
            session = self._get_session(arguments.get("session"))
            return session.to_dict()

        elif name == "parse_formula":
            formula_str = arguments.get("formula", "")
            if not formula_str:
                return {"error": "Formula cannot be empty"}

            formula = FOLFormula(formula_str)
            return formula.get_info()

        elif name == "convert_to_tptp":
            premises = arguments.get("premises", [])
            conclusion = arguments.get("conclusion", "")

            if not premises or not conclusion:
                return {"error": "Both premises and conclusion are required"}

            tptp = self.converter.create_problem(premises, conclusion)
            return {
                "tptp": tptp,
                "format": "TPTP FOF"
            }

        elif name == "list_provers":
            provers = self.prover_manager.list_available_provers()
            return {
                "provers": provers,
                "default": "vampire"
            }

        elif name == "create_session":
            name = arguments.get("name", "")
            if not name:
                return {"error": "Session name is required"}
            if name in self.sessions:
                return {"error": f"Session '{name}' already exists"}

            self.sessions[name] = FOLSession()
            self.sessions[name].name = name
            self.current_session = name
            return {
                "success": True,
                "session": name,
                "message": f"Created and switched to session '{name}'"
            }

        elif name == "list_sessions":
            return {
                "sessions": list(self.sessions.keys()),
                "current": self.current_session
            }

        elif name == "switch_session":
            name = arguments.get("name", "")
            if name not in self.sessions:
                return {"error": f"Session '{name}' not found"}

            self.current_session = name
            return {
                "success": True,
                "current": name,
                "session": self.sessions[name].to_dict()
            }

        elif name == "remove_premise":
            session = self._get_session(arguments.get("session"))
            index = arguments.get("index")

            if index is None:
                return {"error": "Index is required"}

            if session.remove_premise(index):
                return {
                    "success": True,
                    "remaining_premises": len(session.premises)
                }
            return {"error": f"Invalid index: {index}"}

        else:
            return {"error": f"Unknown tool: {name}"}

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Entry point for the FOL Prover MCP server."""
    import asyncio

    server = FOLProverMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
