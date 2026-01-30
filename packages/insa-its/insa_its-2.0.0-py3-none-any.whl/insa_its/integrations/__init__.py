"""
InsAIts Integrations
====================
Native integrations for popular AI frameworks.

Available integrations:
- LangChain: LangChainMonitor, monitor_langchain_chain
- CrewAI: CrewAIMonitor, monitor_crew
- AutoGPT: (coming soon)

Usage:
    from insa_its.integrations import LangChainMonitor, CrewAIMonitor
"""

from .langchain import LangChainMonitor, monitor_langchain_chain
from .crewai import CrewAIMonitor, monitor_crew

__all__ = [
    'LangChainMonitor',
    'monitor_langchain_chain',
    'CrewAIMonitor',
    'monitor_crew',
]
