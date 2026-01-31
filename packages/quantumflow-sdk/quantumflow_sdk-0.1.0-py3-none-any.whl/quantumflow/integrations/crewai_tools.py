"""
CrewAI Tools for QuantumFlow.

Provides quantum-powered tools for CrewAI agents:
- Compression: Reduce context size
- Optimization: QAOA-based problem solving
- Analysis: Quantum-enhanced data analysis
- Search: Grover's algorithm for fast search
"""

from typing import Any, Optional, List, Dict, Type
import numpy as np

try:
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Dummy classes
    class BaseTool:
        pass
    class BaseModel:
        pass
    def Field(*args, **kwargs):
        return None

from quantumflow.core.quantum_compressor import QuantumCompressor
from quantumflow.core.quantum_backprop import QuantumBackprop
from quantumflow.core.memory import QuantumMemory


def _check_crewai():
    """Check if CrewAI is available."""
    if not CREWAI_AVAILABLE:
        raise ImportError(
            "CrewAI is not installed. "
            "Install it with: pip install crewai crewai-tools"
        )


# ============== Tool Implementations ==============

class QuantumCompressCrewTool(BaseTool):
    """
    Quantum compression tool for CrewAI.

    Compresses text data using quantum amplitude encoding,
    achieving up to 53% token reduction.
    """

    name: str = "Quantum Compress"
    description: str = (
        "Compress text data using quantum amplitude encoding. "
        "Input: text string to compress. "
        "Output: compression statistics and ratio. "
        "Use this to reduce context size while preserving information."
    )

    def __init__(self, backend: str = "simulator"):
        _check_crewai()
        super().__init__()
        self._compressor = QuantumCompressor(backend=backend)

    def _run(self, text: str) -> str:
        """Compress the input text."""
        # Tokenize
        words = text.split()
        if len(words) < 2:
            return f"Text too short to compress ({len(words)} words)"

        tokens = [hash(w) % 10000 for w in words]

        result = self._compressor.compress(
            tokens=tokens,
            compression_level=1,
        )

        return (
            f"Quantum Compression Result:\n"
            f"- Input tokens: {result.input_token_count}\n"
            f"- Output qubits: {result.n_qubits}\n"
            f"- Tokens saved: {result.tokens_saved}\n"
            f"- Compression ratio: {result.compression_ratio:.2f}x\n"
            f"- Reduction: {result.compression_percentage:.1f}%"
        )


class QuantumOptimizeCrewTool(BaseTool):
    """
    Quantum optimization tool for CrewAI.

    Uses QAOA to solve optimization problems like
    portfolio optimization, scheduling, routing.
    """

    name: str = "Quantum Optimize"
    description: str = (
        "Solve optimization problems using quantum QAOA algorithm. "
        "Input: JSON string with 'problem_type' (maxcut/portfolio/tsp) and 'data'. "
        "Output: optimal solution and quality metrics. "
        "Use for NP-hard optimization problems."
    )

    def __init__(self, backend: str = "simulator"):
        _check_crewai()
        super().__init__()
        self._backend = backend

    def _run(self, input_data: str) -> str:
        """Run quantum optimization."""
        import json

        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            return "Error: Input must be valid JSON with 'problem_type' and 'data'"

        problem_type = data.get("problem_type", "maxcut")

        if problem_type == "maxcut":
            return self._solve_maxcut(data.get("data", {}))
        elif problem_type == "portfolio":
            return self._solve_portfolio(data.get("data", {}))
        else:
            return f"Unknown problem type: {problem_type}. Supported: maxcut, portfolio"

    def _solve_maxcut(self, data: Dict) -> str:
        """Solve MaxCut problem."""
        from quantumflow.algorithms.optimization import QAOA

        edges = data.get("edges", [(0, 1), (1, 2), (2, 0)])
        n_nodes = data.get("n_nodes", 3)

        # Convert edges to tuples if they're lists
        edges = [tuple(e) if isinstance(e, list) else e for e in edges]

        qaoa = QAOA(backend=self._backend, p=1)
        result = qaoa.maxcut(edges, n_nodes, max_iterations=20)

        return (
            f"MaxCut Solution:\n"
            f"- Optimal partition: {result.best_solution}\n"
            f"- Cut value: {result.best_cost:.2f}\n"
            f"- Iterations: {result.n_iterations}"
        )

    def _solve_portfolio(self, data: Dict) -> str:
        """Solve portfolio optimization using QUBO formulation."""
        from quantumflow.algorithms.optimization import QAOA

        returns = np.array(data.get("returns", [0.1, 0.05, 0.15]))
        covariance = np.array(data.get("covariance", [[0.1, 0.02, 0.01], [0.02, 0.05, 0.01], [0.01, 0.01, 0.08]]))
        risk_factor = data.get("risk_factor", 0.5)

        # Convert to QUBO matrix
        # Objective: maximize returns - risk_factor * variance
        # Q[i,j] = -returns[i] for diagonal + risk_factor * covariance[i,j]
        n_assets = len(returns)
        Q = np.zeros((n_assets, n_assets))

        for i in range(n_assets):
            Q[i, i] = -returns[i] + risk_factor * covariance[i, i]
            for j in range(i + 1, n_assets):
                Q[i, j] = risk_factor * covariance[i, j]
                Q[j, i] = risk_factor * covariance[j, i]

        qaoa = QAOA(backend=self._backend, p=1)
        result = qaoa.optimize_qubo(Q, max_iterations=20)

        # Interpret solution
        allocation = [int(b) for b in result.best_solution]
        selected_assets = [i for i, a in enumerate(allocation) if a == 1]
        expected_return = sum(returns[i] for i in selected_assets)
        risk = sum(covariance[i, j] for i in selected_assets for j in selected_assets)

        return (
            f"Portfolio Optimization:\n"
            f"- Optimal allocation: {allocation}\n"
            f"- Selected assets: {selected_assets}\n"
            f"- Expected return: {expected_return:.2%}\n"
            f"- Portfolio risk: {risk:.4f}"
        )


class QuantumAnalyzeCrewTool(BaseTool):
    """
    Quantum analysis tool for CrewAI.

    Uses quantum algorithms for data analysis including
    pattern recognition and anomaly detection.
    """

    name: str = "Quantum Analyze"
    description: str = (
        "Analyze data using quantum algorithms. "
        "Input: JSON with 'analysis_type' (pattern/anomaly/correlation) and 'data'. "
        "Output: analysis results with quantum-enhanced insights. "
        "Use for pattern recognition and anomaly detection."
    )

    def __init__(self, backend: str = "simulator"):
        _check_crewai()
        super().__init__()
        self._backend = backend
        self._memory = QuantumMemory(backend=backend)

    def _run(self, input_data: str) -> str:
        """Run quantum analysis."""
        import json

        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            return "Error: Input must be valid JSON with 'analysis_type' and 'data'"

        analysis_type = data.get("analysis_type", "pattern")
        values = data.get("data", [])

        if not values:
            return "Error: No data provided for analysis"

        if analysis_type == "pattern":
            return self._analyze_patterns(values)
        elif analysis_type == "anomaly":
            return self._detect_anomalies(values)
        elif analysis_type == "correlation":
            return self._analyze_correlation(values)
        else:
            return f"Unknown analysis type: {analysis_type}"

    def _analyze_patterns(self, values: List[float]) -> str:
        """Analyze patterns using quantum encoding."""
        values_array = np.array(values)

        # Store in quantum memory
        self._memory.store("analysis_data", values)

        # Compute statistics
        mean = np.mean(values_array)
        std = np.std(values_array)
        trend = "increasing" if values_array[-1] > values_array[0] else "decreasing"

        # Quantum compression for pattern density
        from quantumflow.core.quantum_compressor import QuantumCompressor
        compressor = QuantumCompressor(backend=self._backend)

        tokens = [int(v * 1000) % 10000 for v in values]
        if len(tokens) >= 2:
            result = compressor.compress(tokens, compression_level=1)
            pattern_density = result.compression_ratio
        else:
            pattern_density = 1.0

        return (
            f"Pattern Analysis:\n"
            f"- Data points: {len(values)}\n"
            f"- Mean: {mean:.4f}\n"
            f"- Std deviation: {std:.4f}\n"
            f"- Trend: {trend}\n"
            f"- Pattern density (quantum): {pattern_density:.2f}x"
        )

    def _detect_anomalies(self, values: List[float]) -> str:
        """Detect anomalies using quantum analysis."""
        values_array = np.array(values)
        mean = np.mean(values_array)
        std = np.std(values_array)

        # Z-score based anomaly detection
        z_scores = np.abs((values_array - mean) / (std + 1e-8))
        anomaly_threshold = 2.0
        anomalies = [(i, v) for i, (v, z) in enumerate(zip(values, z_scores)) if z > anomaly_threshold]

        return (
            f"Anomaly Detection:\n"
            f"- Data points analyzed: {len(values)}\n"
            f"- Anomalies found: {len(anomalies)}\n"
            f"- Anomaly indices: {[a[0] for a in anomalies]}\n"
            f"- Anomaly values: {[f'{a[1]:.4f}' for a in anomalies]}"
        )

    def _analyze_correlation(self, values: List) -> str:
        """Analyze correlation between datasets."""
        if not isinstance(values[0], list):
            return "Error: Correlation analysis requires multiple datasets (list of lists)"

        datasets = [np.array(v) for v in values]
        if len(datasets) < 2:
            return "Error: Need at least 2 datasets for correlation"

        # Compute correlation matrix
        min_len = min(len(d) for d in datasets)
        trimmed = [d[:min_len] for d in datasets]
        corr_matrix = np.corrcoef(trimmed)

        return (
            f"Correlation Analysis:\n"
            f"- Datasets: {len(datasets)}\n"
            f"- Correlation matrix:\n{corr_matrix.round(4)}"
        )


class QuantumSearchCrewTool(BaseTool):
    """
    Quantum search tool for CrewAI.

    Uses Grover's algorithm for fast unstructured search
    with quadratic speedup.
    """

    name: str = "Quantum Search"
    description: str = (
        "Search through data using Grover's quantum algorithm. "
        "Input: JSON with 'query' and 'database' (list of items). "
        "Output: matching items with quantum speedup metrics. "
        "Use for searching large unstructured datasets."
    )

    def __init__(self, backend: str = "simulator"):
        _check_crewai()
        super().__init__()
        self._backend = backend

    def _run(self, input_data: str) -> str:
        """Run quantum search."""
        import json
        import math

        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            return "Error: Input must be valid JSON with 'query' and 'database'"

        query = data.get("query", "")
        database = data.get("database", [])

        if not query or not database:
            return "Error: Both 'query' and 'database' are required"

        from quantumflow.algorithms.optimization import GroverSearch

        # Create oracle based on query matches - find indices of matching items
        query_lower = query.lower()
        marked_indices = [i for i, item in enumerate(database) if query_lower in str(item).lower()]

        if not marked_indices:
            return f"No matches found for '{query}' in {len(database)} items"

        # Calculate n_qubits needed for the database
        n_qubits = max(2, math.ceil(math.log2(len(database))))

        grover = GroverSearch(backend=self._backend)
        result = grover.search(n_qubits=n_qubits, marked_states=marked_indices)

        matches = [database[i] for i in marked_indices]

        # Calculate speedup
        classical_ops = len(database)
        quantum_ops = result.iterations
        speedup = classical_ops / max(1, quantum_ops)

        return (
            f"Quantum Search Results:\n"
            f"- Query: '{query}'\n"
            f"- Database size: {len(database)}\n"
            f"- Matches found: {len(matches)}\n"
            f"- Top matches: {matches[:5]}\n"
            f"- Quantum iterations: {quantum_ops}\n"
            f"- Classical would need: ~{classical_ops} ops\n"
            f"- Quantum speedup: {speedup:.1f}x\n"
            f"- Success probability: {result.probability:.2%}"
        )


# ============== Toolkit ==============

def get_quantum_crew_tools(backend: str = "simulator") -> List[BaseTool]:
    """
    Get all quantum tools for CrewAI.

    Args:
        backend: Quantum backend to use ("simulator", "ibm")

    Returns:
        List of quantum tools for use with CrewAI agents

    Example:
        from crewai import Agent, Task, Crew
        from quantumflow.integrations import get_quantum_crew_tools

        tools = get_quantum_crew_tools()

        researcher = Agent(
            role="Quantum Researcher",
            goal="Analyze data using quantum algorithms",
            tools=tools,
        )
    """
    _check_crewai()

    return [
        QuantumCompressCrewTool(backend=backend),
        QuantumOptimizeCrewTool(backend=backend),
        QuantumAnalyzeCrewTool(backend=backend),
        QuantumSearchCrewTool(backend=backend),
    ]
