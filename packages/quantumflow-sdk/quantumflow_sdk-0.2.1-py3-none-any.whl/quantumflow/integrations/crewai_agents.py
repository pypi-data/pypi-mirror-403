"""
CrewAI Agents for QuantumFlow.

Pre-configured quantum-enhanced agents for common tasks:
- QuantumResearchAgent: Research and analysis
- QuantumOptimizerAgent: Optimization tasks
- QuantumAnalystAgent: Data analysis
"""

from typing import Any, Optional, List, Dict

try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Dummy classes
    class Agent:
        pass
    class Task:
        pass
    class Crew:
        pass

from quantumflow.integrations.crewai_tools import (
    get_quantum_crew_tools,
    QuantumCompressCrewTool,
    QuantumOptimizeCrewTool,
    QuantumAnalyzeCrewTool,
    QuantumSearchCrewTool,
)


def _check_crewai():
    """Check if CrewAI is available."""
    if not CREWAI_AVAILABLE:
        raise ImportError(
            "CrewAI is not installed. "
            "Install it with: pip install crewai crewai-tools"
        )


class QuantumResearchAgent:
    """
    Quantum-enhanced research agent.

    Specializes in:
    - Literature search with quantum speedup
    - Data compression for large contexts
    - Pattern recognition in research data

    Example:
        from quantumflow.integrations import QuantumResearchAgent

        agent = QuantumResearchAgent.create(llm=my_llm)
        # Use with CrewAI tasks
    """

    @classmethod
    def create(
        cls,
        llm: Any = None,
        backend: str = "simulator",
        verbose: bool = True,
        **kwargs
    ) -> Agent:
        """
        Create a quantum research agent.

        Args:
            llm: Language model to use
            backend: Quantum backend ("simulator" or "ibm")
            verbose: Enable verbose output
            **kwargs: Additional Agent parameters

        Returns:
            CrewAI Agent configured for quantum research
        """
        _check_crewai()

        tools = [
            QuantumSearchCrewTool(backend=backend),
            QuantumCompressCrewTool(backend=backend),
            QuantumAnalyzeCrewTool(backend=backend),
        ]

        agent_kwargs = {
            "role": "Quantum Research Specialist",
            "goal": (
                "Conduct thorough research using quantum-enhanced search and analysis. "
                "Leverage Grover's algorithm for fast information retrieval and "
                "quantum compression for handling large datasets efficiently."
            ),
            "backstory": (
                "You are an expert researcher with access to quantum computing tools. "
                "You can search through vast databases with quadratic speedup using "
                "Grover's algorithm, compress large contexts using quantum amplitude "
                "encoding, and identify patterns using quantum analysis. Your quantum "
                "tools give you an edge in processing and analyzing information faster "
                "than classical methods."
            ),
            "tools": tools,
            "verbose": verbose,
            "allow_delegation": True,
        }

        if llm:
            agent_kwargs["llm"] = llm

        agent_kwargs.update(kwargs)
        return Agent(**agent_kwargs)


class QuantumOptimizerAgent:
    """
    Quantum-enhanced optimization agent.

    Specializes in:
    - QAOA for combinatorial optimization
    - Portfolio optimization
    - Resource allocation
    - Scheduling problems

    Example:
        from quantumflow.integrations import QuantumOptimizerAgent

        agent = QuantumOptimizerAgent.create(llm=my_llm)
    """

    @classmethod
    def create(
        cls,
        llm: Any = None,
        backend: str = "simulator",
        verbose: bool = True,
        **kwargs
    ) -> Agent:
        """
        Create a quantum optimization agent.

        Args:
            llm: Language model to use
            backend: Quantum backend
            verbose: Enable verbose output

        Returns:
            CrewAI Agent configured for quantum optimization
        """
        _check_crewai()

        tools = [
            QuantumOptimizeCrewTool(backend=backend),
            QuantumAnalyzeCrewTool(backend=backend),
        ]

        agent_kwargs = {
            "role": "Quantum Optimization Expert",
            "goal": (
                "Solve complex optimization problems using quantum algorithms. "
                "Apply QAOA for NP-hard problems like portfolio optimization, "
                "scheduling, routing, and resource allocation."
            ),
            "backstory": (
                "You are a quantum optimization specialist with deep expertise in "
                "the Quantum Approximate Optimization Algorithm (QAOA). You can "
                "tackle combinatorial optimization problems that are intractable "
                "for classical computers. Your toolkit includes solvers for MaxCut, "
                "portfolio optimization, traveling salesman, and other NP-hard problems. "
                "You understand the trade-offs between solution quality and quantum "
                "resources, and can recommend the best approach for each problem."
            ),
            "tools": tools,
            "verbose": verbose,
            "allow_delegation": False,
        }

        if llm:
            agent_kwargs["llm"] = llm

        agent_kwargs.update(kwargs)
        return Agent(**agent_kwargs)


class QuantumAnalystAgent:
    """
    Quantum-enhanced data analyst agent.

    Specializes in:
    - Pattern recognition
    - Anomaly detection
    - Correlation analysis
    - Data compression

    Example:
        from quantumflow.integrations import QuantumAnalystAgent

        agent = QuantumAnalystAgent.create(llm=my_llm)
    """

    @classmethod
    def create(
        cls,
        llm: Any = None,
        backend: str = "simulator",
        verbose: bool = True,
        **kwargs
    ) -> Agent:
        """
        Create a quantum analyst agent.

        Args:
            llm: Language model to use
            backend: Quantum backend
            verbose: Enable verbose output

        Returns:
            CrewAI Agent configured for quantum analysis
        """
        _check_crewai()

        tools = [
            QuantumAnalyzeCrewTool(backend=backend),
            QuantumCompressCrewTool(backend=backend),
            QuantumSearchCrewTool(backend=backend),
        ]

        agent_kwargs = {
            "role": "Quantum Data Analyst",
            "goal": (
                "Analyze data using quantum-enhanced techniques. "
                "Detect patterns, identify anomalies, and find correlations "
                "that classical methods might miss."
            ),
            "backstory": (
                "You are a data analyst empowered with quantum computing tools. "
                "Your quantum analysis capabilities allow you to find hidden patterns "
                "in data through quantum amplitude encoding, detect anomalies using "
                "quantum-enhanced statistical methods, and compress large datasets "
                "while preserving essential information. You excel at extracting "
                "insights from complex, high-dimensional data."
            ),
            "tools": tools,
            "verbose": verbose,
            "allow_delegation": True,
        }

        if llm:
            agent_kwargs["llm"] = llm

        agent_kwargs.update(kwargs)
        return Agent(**agent_kwargs)


def create_quantum_crew(
    llm: Any = None,
    backend: str = "simulator",
    tasks: Optional[List[Dict[str, Any]]] = None,
    process: str = "sequential",
    verbose: bool = True,
) -> Crew:
    """
    Create a complete quantum-enhanced crew.

    Creates a team with:
    - Quantum Research Specialist
    - Quantum Optimization Expert
    - Quantum Data Analyst

    Args:
        llm: Language model for all agents
        backend: Quantum backend
        tasks: Optional list of task definitions
        process: Crew process type ("sequential" or "hierarchical")
        verbose: Enable verbose output

    Returns:
        CrewAI Crew with quantum-enhanced agents

    Example:
        from quantumflow.integrations import create_quantum_crew

        crew = create_quantum_crew(
            llm=my_llm,
            tasks=[
                {
                    "description": "Research quantum computing trends",
                    "agent": "researcher",
                    "expected_output": "A summary of trends"
                },
                {
                    "description": "Optimize resource allocation",
                    "agent": "optimizer",
                    "expected_output": "Optimal allocation plan"
                }
            ]
        )
        result = crew.kickoff()
    """
    _check_crewai()

    # Create agents
    researcher = QuantumResearchAgent.create(llm=llm, backend=backend, verbose=verbose)
    optimizer = QuantumOptimizerAgent.create(llm=llm, backend=backend, verbose=verbose)
    analyst = QuantumAnalystAgent.create(llm=llm, backend=backend, verbose=verbose)

    agents = {
        "researcher": researcher,
        "optimizer": optimizer,
        "analyst": analyst,
    }

    # Create tasks if provided
    crew_tasks = []
    if tasks:
        for task_def in tasks:
            agent_key = task_def.get("agent", "researcher")
            agent = agents.get(agent_key, researcher)

            task = Task(
                description=task_def.get("description", ""),
                expected_output=task_def.get("expected_output", "Analysis complete"),
                agent=agent,
            )
            crew_tasks.append(task)

    # Create crew
    process_type = Process.sequential if process == "sequential" else Process.hierarchical

    return Crew(
        agents=list(agents.values()),
        tasks=crew_tasks,
        process=process_type,
        verbose=verbose,
    )


# ============== Pre-built Task Templates ==============

class QuantumTaskTemplates:
    """Pre-built task templates for common quantum workflows."""

    @staticmethod
    def research_task(
        topic: str,
        agent: Agent,
        context: Optional[str] = None,
    ) -> Task:
        """Create a research task."""
        _check_crewai()

        description = f"""
        Research the following topic using quantum-enhanced search: {topic}

        Steps:
        1. Use Quantum Search to find relevant information
        2. Use Quantum Compress to handle large contexts
        3. Use Quantum Analyze to identify patterns

        {f'Additional context: {context}' if context else ''}
        """

        return Task(
            description=description,
            expected_output="Comprehensive research summary with key findings and insights",
            agent=agent,
        )

    @staticmethod
    def optimization_task(
        problem: str,
        agent: Agent,
        constraints: Optional[Dict] = None,
    ) -> Task:
        """Create an optimization task."""
        _check_crewai()

        constraints_str = ""
        if constraints:
            constraints_str = "\n".join(f"- {k}: {v}" for k, v in constraints.items())

        description = f"""
        Solve the following optimization problem using quantum QAOA: {problem}

        {'Constraints:' + constraints_str if constraints_str else ''}

        Steps:
        1. Formulate the problem for QAOA
        2. Use Quantum Optimize to find optimal solution
        3. Verify solution quality and constraints
        """

        return Task(
            description=description,
            expected_output="Optimal solution with quality metrics and constraint satisfaction",
            agent=agent,
        )

    @staticmethod
    def analysis_task(
        data_description: str,
        agent: Agent,
        analysis_types: Optional[List[str]] = None,
    ) -> Task:
        """Create an analysis task."""
        _check_crewai()

        types = analysis_types or ["pattern", "anomaly", "correlation"]
        types_str = ", ".join(types)

        description = f"""
        Analyze the following data using quantum techniques: {data_description}

        Analysis types to perform: {types_str}

        Steps:
        1. Use Quantum Analyze for each analysis type
        2. Identify key patterns and anomalies
        3. Summarize findings with quantum-enhanced insights
        """

        return Task(
            description=description,
            expected_output="Detailed analysis report with patterns, anomalies, and correlations",
            agent=agent,
        )
