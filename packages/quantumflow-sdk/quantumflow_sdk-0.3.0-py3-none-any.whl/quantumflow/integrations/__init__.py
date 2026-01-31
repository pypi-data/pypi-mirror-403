"""
QuantumFlow Integrations.

Provides integration with popular AI agent frameworks:
- OpenAI: Function calling for GPT-4/GPT-3.5-turbo
- LangChain: Tools, Memory, and Chains
- CrewAI: Tools and Agents
- AutoGen: Agents and Function Tools
- MCP: Model Context Protocol Server
"""

# OpenAI Integration
from quantumflow.integrations.openai_functions import (
    get_quantum_functions as get_openai_functions,
    get_quantum_tools as get_openai_tools,
    execute_quantum_function,
    QuantumAssistant,
)

# LangChain Integration
from quantumflow.integrations.langchain_tools import (
    QuantumCompressTool,
    QuantumGradientTool,
    QuantumMemoryTool,
    QuantumEntangleTool,
    QuantumSearchTool,
    get_quantum_toolkit,
)

from quantumflow.integrations.langchain_memory import (
    QuantumChatMemory,
    QuantumVectorStore,
)

# CrewAI Integration
from quantumflow.integrations.crewai_tools import (
    QuantumCompressCrewTool,
    QuantumOptimizeCrewTool,
    QuantumAnalyzeCrewTool,
    QuantumSearchCrewTool,
    get_quantum_crew_tools,
)

from quantumflow.integrations.crewai_agents import (
    QuantumResearchAgent,
    QuantumOptimizerAgent,
    QuantumAnalystAgent,
    create_quantum_crew,
)

# AutoGen Integration
from quantumflow.integrations.autogen_tools import (
    quantum_compress,
    quantum_gradient,
    quantum_memory_store,
    quantum_memory_retrieve,
    quantum_search,
    quantum_optimize,
    quantum_entangle,
    get_quantum_functions,
    register_quantum_functions,
    create_quantum_assistant,
    create_quantum_researcher,
    create_quantum_optimizer,
    create_quantum_group_chat,
)

# MCP Integration
from quantumflow.integrations.mcp_server import (
    QuantumMCPServer,
    create_mcp_server,
    get_mcp_config,
)

__all__ = [
    # OpenAI Functions
    "get_openai_functions",
    "get_openai_tools",
    "execute_quantum_function",
    "QuantumAssistant",
    # LangChain Tools
    "QuantumCompressTool",
    "QuantumGradientTool",
    "QuantumMemoryTool",
    "QuantumEntangleTool",
    "QuantumSearchTool",
    "get_quantum_toolkit",
    # LangChain Memory
    "QuantumChatMemory",
    "QuantumVectorStore",
    # CrewAI Tools
    "QuantumCompressCrewTool",
    "QuantumOptimizeCrewTool",
    "QuantumAnalyzeCrewTool",
    "QuantumSearchCrewTool",
    "get_quantum_crew_tools",
    # CrewAI Agents
    "QuantumResearchAgent",
    "QuantumOptimizerAgent",
    "QuantumAnalystAgent",
    "create_quantum_crew",
    # AutoGen Functions
    "quantum_compress",
    "quantum_gradient",
    "quantum_memory_store",
    "quantum_memory_retrieve",
    "quantum_search",
    "quantum_optimize",
    "quantum_entangle",
    "get_quantum_functions",
    "register_quantum_functions",
    # AutoGen Agents
    "create_quantum_assistant",
    "create_quantum_researcher",
    "create_quantum_optimizer",
    "create_quantum_group_chat",
    # MCP Server
    "QuantumMCPServer",
    "create_mcp_server",
    "get_mcp_config",
]
