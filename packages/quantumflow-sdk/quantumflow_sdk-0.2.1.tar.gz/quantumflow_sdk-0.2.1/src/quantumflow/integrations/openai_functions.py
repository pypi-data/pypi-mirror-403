"""
OpenAI Function Calling Integration for QuantumFlow.

Provides function definitions and execution handlers compatible with
OpenAI's function calling API (GPT-4, GPT-3.5-turbo).

Usage:
    from openai import OpenAI
    from quantumflow.integrations.openai_functions import (
        get_quantum_functions,
        execute_quantum_function,
    )

    client = OpenAI()
    functions = get_quantum_functions()

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Compress these tokens: 100, 200, 150"}],
        functions=functions,
        function_call="auto",
    )

    # Execute the function call
    if response.choices[0].message.function_call:
        result = execute_quantum_function(
            response.choices[0].message.function_call.name,
            json.loads(response.choices[0].message.function_call.arguments)
        )
"""

import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass

from quantumflow.core.quantum_compressor import QuantumCompressor
from quantumflow.core.quantum_backprop import QuantumBackprop
from quantumflow.core.teleportation import QuantumTeleporter, QKDExchange, SecureMessenger
from quantumflow.core.entanglement import Entangler
from quantumflow.core.memory import QuantumMemory


# OpenAI Function Definitions
QUANTUM_FUNCTIONS: List[Dict[str, Any]] = [
    {
        "name": "quantum_compress",
        "description": "Compress a list of token values using quantum amplitude encoding. Achieves ~53% compression while preserving semantic information.",
        "parameters": {
            "type": "object",
            "properties": {
                "tokens": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of token values (integers or floats) to compress",
                },
                "backend": {
                    "type": "string",
                    "enum": ["simulator", "ibm", "aws"],
                    "description": "Quantum backend to use. Default: simulator",
                },
            },
            "required": ["tokens"],
        },
    },
    {
        "name": "quantum_decompress",
        "description": "Decompress previously quantum-compressed data back to original tokens.",
        "parameters": {
            "type": "object",
            "properties": {
                "compressed_state": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "The compressed quantum state amplitudes",
                },
                "n_qubits": {
                    "type": "integer",
                    "description": "Number of qubits used in compression",
                },
                "original_length": {
                    "type": "integer",
                    "description": "Original number of tokens",
                },
            },
            "required": ["compressed_state", "n_qubits", "original_length"],
        },
    },
    {
        "name": "quantum_gradient",
        "description": "Compute gradients using quantum backpropagation via teleportation protocol. Achieves 97.78% gradient similarity with classical methods.",
        "parameters": {
            "type": "object",
            "properties": {
                "weights": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Neural network weights to compute gradients for",
                },
                "loss_value": {
                    "type": "number",
                    "description": "Current loss value",
                },
                "learning_rate": {
                    "type": "number",
                    "description": "Learning rate for gradient computation. Default: 0.01",
                },
            },
            "required": ["weights", "loss_value"],
        },
    },
    {
        "name": "quantum_entangle",
        "description": "Create quantum entanglement between data points for correlation analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "data_a": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "First data array",
                },
                "data_b": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Second data array",
                },
            },
            "required": ["data_a", "data_b"],
        },
    },
    {
        "name": "quantum_teleport",
        "description": "Teleport quantum state information using entangled Bell pairs.",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Quantum state amplitudes to teleport",
                },
                "n_pairs": {
                    "type": "integer",
                    "description": "Number of Bell pairs to use. Default: 10",
                },
            },
            "required": ["state"],
        },
    },
    {
        "name": "qkd_exchange",
        "description": "Perform BB84 quantum key distribution for unconditionally secure key exchange.",
        "parameters": {
            "type": "object",
            "properties": {
                "key_length": {
                    "type": "integer",
                    "description": "Desired key length in bits. Default: 256",
                },
                "error_threshold": {
                    "type": "number",
                    "description": "Maximum acceptable error rate. Default: 0.11",
                },
            },
            "required": [],
        },
    },
    {
        "name": "secure_message",
        "description": "Send a message using quantum-secure encryption with QKD-generated keys.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to encrypt and send",
                },
                "key_length": {
                    "type": "integer",
                    "description": "Key length for encryption. Default: 256",
                },
            },
            "required": ["message"],
        },
    },
    {
        "name": "quantum_memory_store",
        "description": "Store data in quantum memory with O(log n) space complexity.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Storage key identifier",
                },
                "data": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Data to store",
                },
            },
            "required": ["key", "data"],
        },
    },
    {
        "name": "quantum_memory_retrieve",
        "description": "Retrieve data from quantum memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Storage key identifier",
                },
            },
            "required": ["key"],
        },
    },
]


# Singleton instances for stateful operations
_compressor: Optional[QuantumCompressor] = None
_backprop: Optional[QuantumBackprop] = None
_teleporter: Optional[QuantumTeleporter] = None
_qkd: Optional[QKDExchange] = None
_messenger: Optional[SecureMessenger] = None
_entangler: Optional[Entangler] = None
_memory: Optional[QuantumMemory] = None


def _get_compressor(backend: str = "simulator") -> QuantumCompressor:
    global _compressor
    if _compressor is None:
        _compressor = QuantumCompressor(backend=backend)
    return _compressor


def _get_backprop() -> QuantumBackprop:
    global _backprop
    if _backprop is None:
        _backprop = QuantumBackprop()
    return _backprop


def _get_teleporter() -> QuantumTeleporter:
    global _teleporter
    if _teleporter is None:
        _teleporter = QuantumTeleporter()
    return _teleporter


def _get_qkd() -> QKDExchange:
    global _qkd
    if _qkd is None:
        _qkd = QKDExchange()
    return _qkd


def _get_messenger() -> SecureMessenger:
    global _messenger
    if _messenger is None:
        _messenger = SecureMessenger()
    return _messenger


def _get_entangler() -> Entangler:
    global _entangler
    if _entangler is None:
        _entangler = Entangler()
    return _entangler


def _get_memory() -> QuantumMemory:
    global _memory
    if _memory is None:
        _memory = QuantumMemory()
    return _memory


def get_quantum_functions() -> List[Dict[str, Any]]:
    """
    Get the list of quantum function definitions for OpenAI's function calling API.

    Returns:
        List of function definitions compatible with OpenAI's API.

    Example:
        from openai import OpenAI
        from quantumflow.integrations.openai_functions import get_quantum_functions

        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[...],
            functions=get_quantum_functions(),
            function_call="auto",
        )
    """
    return QUANTUM_FUNCTIONS.copy()


def get_quantum_tools() -> List[Dict[str, Any]]:
    """
    Get the list of quantum tools for OpenAI's tools API (newer format).

    Returns:
        List of tool definitions compatible with OpenAI's tools API.

    Example:
        from openai import OpenAI
        from quantumflow.integrations.openai_functions import get_quantum_tools

        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[...],
            tools=get_quantum_tools(),
            tool_choice="auto",
        )
    """
    return [
        {"type": "function", "function": func}
        for func in QUANTUM_FUNCTIONS
    ]


def execute_quantum_function(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a quantum function by name with the given arguments.

    Args:
        name: The function name to execute.
        arguments: Dictionary of function arguments.

    Returns:
        Dictionary containing the function result.

    Raises:
        ValueError: If the function name is not recognized.

    Example:
        result = execute_quantum_function(
            "quantum_compress",
            {"tokens": [100, 200, 150, 175]}
        )
    """
    handlers: Dict[str, Callable] = {
        "quantum_compress": _handle_compress,
        "quantum_decompress": _handle_decompress,
        "quantum_gradient": _handle_gradient,
        "quantum_entangle": _handle_entangle,
        "quantum_teleport": _handle_teleport,
        "qkd_exchange": _handle_qkd,
        "secure_message": _handle_secure_message,
        "quantum_memory_store": _handle_memory_store,
        "quantum_memory_retrieve": _handle_memory_retrieve,
    }

    if name not in handlers:
        raise ValueError(f"Unknown quantum function: {name}")

    return handlers[name](arguments)


def _handle_compress(args: Dict[str, Any]) -> Dict[str, Any]:
    tokens = args["tokens"]
    backend = args.get("backend", "simulator")
    compressor = _get_compressor(backend)
    result = compressor.compress(tokens)
    return {
        "success": True,
        "compressed_state": result.amplitudes.tolist() if hasattr(result.amplitudes, 'tolist') else list(result.amplitudes),
        "n_qubits": result.n_qubits,
        "original_length": len(tokens),
        "compression_percentage": result.compression_percentage,
        "fidelity": result.fidelity,
    }


def _handle_decompress(args: Dict[str, Any]) -> Dict[str, Any]:
    compressor = _get_compressor()
    result = compressor.decompress(
        compressed_state=args["compressed_state"],
        n_qubits=args["n_qubits"],
        original_length=args["original_length"],
    )
    return {
        "success": True,
        "tokens": result.tolist() if hasattr(result, 'tolist') else list(result),
    }


def _handle_gradient(args: Dict[str, Any]) -> Dict[str, Any]:
    backprop = _get_backprop()
    weights = args["weights"]
    loss = args["loss_value"]
    lr = args.get("learning_rate", 0.01)
    result = backprop.compute_gradients(weights, loss, learning_rate=lr)
    return {
        "success": True,
        "gradients": result.gradients.tolist() if hasattr(result.gradients, 'tolist') else list(result.gradients),
        "similarity": result.similarity,
        "teleportation_fidelity": result.fidelity,
    }


def _handle_entangle(args: Dict[str, Any]) -> Dict[str, Any]:
    entangler = _get_entangler()
    result = entangler.entangle(args["data_a"], args["data_b"])
    return {
        "success": True,
        "correlation": result.correlation,
        "bell_state": result.bell_state,
        "fidelity": result.fidelity,
    }


def _handle_teleport(args: Dict[str, Any]) -> Dict[str, Any]:
    teleporter = _get_teleporter()
    n_pairs = args.get("n_pairs", 10)
    result = teleporter.teleport(args["state"], n_pairs=n_pairs)
    return {
        "success": True,
        "teleported_state": result.state.tolist() if hasattr(result.state, 'tolist') else list(result.state),
        "fidelity": result.fidelity,
        "bell_pairs_used": n_pairs,
    }


def _handle_qkd(args: Dict[str, Any]) -> Dict[str, Any]:
    qkd = _get_qkd()
    key_length = args.get("key_length", 256)
    error_threshold = args.get("error_threshold", 0.11)
    result = qkd.exchange(key_length=key_length, error_threshold=error_threshold)
    return {
        "success": True,
        "key": result.key,
        "key_length": len(result.key),
        "error_rate": result.error_rate,
        "secure": result.secure,
    }


def _handle_secure_message(args: Dict[str, Any]) -> Dict[str, Any]:
    messenger = _get_messenger()
    message = args["message"]
    key_length = args.get("key_length", 256)
    result = messenger.send_message(message, key_length=key_length)
    return {
        "success": True,
        "encrypted": result.encrypted,
        "message_hash": result.message_hash,
        "key_id": result.key_id,
    }


def _handle_memory_store(args: Dict[str, Any]) -> Dict[str, Any]:
    memory = _get_memory()
    key = args["key"]
    data = args["data"]
    memory.store(key, data)
    return {
        "success": True,
        "key": key,
        "stored_length": len(data),
        "quantum_bits_used": memory.get_usage(key),
    }


def _handle_memory_retrieve(args: Dict[str, Any]) -> Dict[str, Any]:
    memory = _get_memory()
    key = args["key"]
    data = memory.retrieve(key)
    if data is None:
        return {
            "success": False,
            "error": f"Key '{key}' not found in quantum memory",
        }
    return {
        "success": True,
        "key": key,
        "data": data.tolist() if hasattr(data, 'tolist') else list(data),
    }


@dataclass
class QuantumAssistant:
    """
    A helper class for integrating QuantumFlow with OpenAI's chat completions.

    Example:
        from openai import OpenAI
        from quantumflow.integrations.openai_functions import QuantumAssistant

        client = OpenAI()
        assistant = QuantumAssistant(client)

        # Chat with quantum capabilities
        response = assistant.chat("Compress these tokens: 100, 200, 150, 175")
        print(response)
    """

    client: Any  # OpenAI client
    model: str = "gpt-4"
    messages: List[Dict[str, str]] = None

    def __post_init__(self):
        if self.messages is None:
            self.messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a quantum computing assistant with access to QuantumFlow tools. "
                        "You can compress tokens, compute quantum gradients, perform quantum key distribution, "
                        "send secure messages, and manage quantum memory. Use these tools to help users "
                        "leverage quantum computing capabilities."
                    ),
                }
            ]

    def chat(self, user_message: str) -> str:
        """
        Send a message and get a response, automatically handling function calls.

        Args:
            user_message: The user's message.

        Returns:
            The assistant's response text.
        """
        self.messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=get_quantum_tools(),
            tool_choice="auto",
        )

        message = response.choices[0].message

        # Handle tool calls
        while message.tool_calls:
            self.messages.append(message)

            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                try:
                    result = execute_quantum_function(function_name, arguments)
                    tool_response = json.dumps(result)
                except Exception as e:
                    tool_response = json.dumps({"error": str(e)})

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_response,
                })

            # Get next response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=get_quantum_tools(),
                tool_choice="auto",
            )
            message = response.choices[0].message

        # Final response
        self.messages.append({"role": "assistant", "content": message.content})
        return message.content

    def reset(self):
        """Reset the conversation history."""
        self.__post_init__()
