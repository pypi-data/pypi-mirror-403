# QuantumFlow SDK

Quantum-optimized AI agent workflow platform with 53% token compression, quantum teleportation, and BB84 QKD.

## Installation

```bash
pip install quantumflow-sdk
```

With IBM Quantum support:
```bash
pip install quantumflow-sdk[ibm]
```

With all integrations:
```bash
pip install quantumflow-sdk[all]
```

## Quick Start

### Token Compression

```python
from quantumflow import QuantumCompressor

compressor = QuantumCompressor(backend="simulator")
result = compressor.compress([100, 200, 150, 175, 225, 180, 160, 190])

print(f"Input tokens: {result.input_token_count}")
print(f"Output qubits: {result.n_qubits}")
print(f"Compression: {result.compression_percentage:.1f}%")
```

### Quantum Backpropagation

```python
from quantumflow import QuantumBackprop

backprop = QuantumBackprop(backend="simulator")
result = backprop.compute_gradient(
    input_state=[0.5, 0.5],
    target_state=[0.8, 0.2],
    weights=[0.3, 0.7],
)

print(f"Gradients: {result.gradients}")
print(f"Similarity: {result.similarity:.2%}")
```

### Quantum Key Distribution (QKD)

```python
from quantumflow import QKDExchange

qkd = QKDExchange(backend="simulator")
result = qkd.exchange(key_length=256)

print(f"Shared key: {result['key'][:32]}...")
print(f"Error rate: {result['error_rate']:.2%}")
print(f"Secure: {result['secure']}")
```

### Quantum Teleportation

```python
from quantumflow import QuantumTeleporter

teleporter = QuantumTeleporter(backend="simulator")

# Create Bell pairs
pairs = teleporter.create_bell_pairs(10)

# Teleport a quantum state
state = [0.707 + 0j, 0.707 + 0j]  # |+> state
result = teleporter.teleport_state(state)

print(f"Fidelity: {result.fidelity:.4f}")
print(f"Corrections: {result.corrections_applied}")
```

### Secure Messaging

```python
from quantumflow import SecureMessenger

messenger = SecureMessenger(backend="simulator")

# Establish secure channel
channel = messenger.establish_channel("bob@example.com")

# Send message via compressed teleportation + QKD
result = messenger.send_message("Hello, quantum world!")

print(f"Compression ratio: {result['compression_ratio']:.1f}x")
print(f"QKD secured: {result['qkd_secured']}")
```

## REST API

You can also use the hosted API at `https://api.qflowai.dev`:

```bash
# Token compression
curl -X POST https://api.qflowai.dev/v1/compress \
  -H "Content-Type: application/json" \
  -d '{"tokens": [100, 200, 150, 175]}'

# QKD exchange
curl -X POST https://api.qflowai.dev/v1/quantum/qkd/exchange \
  -H "Content-Type: application/json" \
  -d '{"key_length": 256}'

# Secure message
curl -X POST https://api.qflowai.dev/v1/quantum/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello quantum world!"}'
```

## Features

- **53% Token Compression**: Quantum amplitude encoding for exponential compression
- **Quantum Backpropagation**: 97.78% gradient similarity via teleportation protocol
- **BB84 QKD**: Unconditionally secure key exchange
- **Quantum Teleportation**: State transfer without physical qubit transmission
- **Secure Messaging**: Compressed teleportation + QKD encryption
- **Multi-Backend**: Simulator, IBM Quantum, AWS Braket

## Framework Integrations

- LangChain
- CrewAI
- AutoGen
- Claude MCP

## Documentation

Full documentation at [https://qflowai.dev/docs](https://qflowai.dev/docs)

## License

MIT License - see LICENSE file for details.
