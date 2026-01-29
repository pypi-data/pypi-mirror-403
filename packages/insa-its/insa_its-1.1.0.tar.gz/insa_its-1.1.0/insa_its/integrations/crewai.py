"""
InsAIts CrewAI Integration
==========================
Monitor CrewAI crews and agent interactions automatically.

Usage:
    from crewai import Crew, Agent, Task
    from insa_its.integrations import CrewAIMonitor

    # Create your crew
    agent1 = Agent(name="Researcher", ...)
    agent2 = Agent(name="Writer", ...)
    crew = Crew(agents=[agent1, agent2], tasks=[...])

    # Wrap with InsAIts monitoring
    monitor = CrewAIMonitor(api_key="your-key")
    monitored_crew = monitor.wrap_crew(crew)

    # Run normally - all agent communications are monitored
    result = monitored_crew.kickoff()

    # Check for anomalies
    print(monitor.get_anomalies())
    print(monitor.analyze_crew_health())
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
import time

logger = logging.getLogger(__name__)

# Try importing CrewAI
try:
    from crewai import Crew, Agent, Task
    from crewai.agents.agent_builder.base_agent import BaseAgent
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False


class CrewAIMonitor:
    """
    Main class for monitoring CrewAI crews and agents.

    Features:
    - Automatic agent registration
    - Task execution monitoring
    - Inter-agent communication tracking
    - Anomaly detection across crew
    - Crew health analysis

    Example:
        monitor = CrewAIMonitor(api_key="your-key")
        monitored = monitor.wrap_crew(crew)
        result = monitored.kickoff()

        # Analyze
        print(monitor.get_anomalies())
        print(monitor.analyze_crew_health())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        session_name: Optional[str] = None,
        auto_prevent: bool = True,
        **kwargs
    ):
        """
        Initialize CrewAI monitor.

        Args:
            api_key: InsAIts API key (optional, enables Pro features)
            session_name: Name for this monitoring session
            auto_prevent: Auto-prevent anomalies (Pro feature)
            **kwargs: Additional args passed to insAItsMonitor
        """
        if not CREWAI_AVAILABLE:
            raise ImportError(
                "CrewAI not installed. Install with: pip install crewai"
            )

        # Import here to avoid circular imports
        from ..monitor import insAItsMonitor

        self.insaits = insAItsMonitor(
            api_key=api_key,
            session_name=session_name or "crewai_session",
            auto_prevent=auto_prevent,
            **kwargs
        )
        self._anomalies: List[Dict] = []
        self._task_results: List[Dict] = []
        self._wrapped_crews: List[Any] = []

    def wrap_crew(self, crew: Any) -> Any:
        """
        Wrap a CrewAI Crew with InsAIts monitoring.

        This patches the crew's execution methods to capture
        all agent communications and task results.

        Args:
            crew: CrewAI Crew instance

        Returns:
            The same crew with monitoring enabled
        """
        if not CREWAI_AVAILABLE:
            raise ImportError("CrewAI not available")

        # Register all agents
        for agent in crew.agents:
            agent_name = getattr(agent, 'name', None) or getattr(agent, 'role', 'unknown_agent')
            llm_name = self._extract_llm_name(agent)
            self.insaits.register_agent(agent_name, llm_name)

        # Store original kickoff
        original_kickoff = crew.kickoff

        @wraps(original_kickoff)
        def monitored_kickoff(*args, **kwargs):
            return self._monitored_execution(crew, original_kickoff, *args, **kwargs)

        crew.kickoff = monitored_kickoff
        self._wrapped_crews.append(crew)

        return crew

    def _extract_llm_name(self, agent: Any) -> str:
        """Extract LLM model name from a CrewAI agent."""
        try:
            # Try common attribute paths
            if hasattr(agent, 'llm'):
                llm = agent.llm
                if hasattr(llm, 'model_name'):
                    return llm.model_name
                if hasattr(llm, 'model'):
                    return llm.model
                return str(type(llm).__name__).lower()
            return "unknown"
        except Exception:
            return "unknown"

    def _monitored_execution(
        self,
        crew: Any,
        original_kickoff: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute crew with monitoring."""

        # Track task execution
        start_time = time.time()

        # Patch agent execute methods to capture communications
        original_executes = {}
        for agent in crew.agents:
            agent_name = getattr(agent, 'name', None) or getattr(agent, 'role', 'unknown')
            llm_name = self._extract_llm_name(agent)

            if hasattr(agent, 'execute_task'):
                original_executes[agent_name] = agent.execute_task

                def make_monitored_execute(orig_exec, a_name, l_name):
                    @wraps(orig_exec)
                    def monitored_execute(task, *a, **kw):
                        # Log task start
                        task_desc = getattr(task, 'description', str(task))[:200]
                        self.insaits.send_message(
                            text=f"[Task Started] {task_desc}",
                            sender_id="crew_manager",
                            receiver_id=a_name,
                            llm_id="system"
                        )

                        # Execute task
                        result = orig_exec(task, *a, **kw)

                        # Log result
                        result_text = str(result)[:500] if result else "No output"
                        msg_result = self.insaits.send_message(
                            text=result_text,
                            sender_id=a_name,
                            receiver_id="crew_manager",
                            llm_id=l_name
                        )

                        # Track anomalies
                        if msg_result.get("anomalies"):
                            self._anomalies.extend(msg_result["anomalies"])

                        return result

                    return monitored_execute

                agent.execute_task = make_monitored_execute(
                    original_executes[agent_name],
                    agent_name,
                    llm_name
                )

        try:
            # Run the crew
            result = original_kickoff(*args, **kwargs)

            # Log completion
            elapsed = time.time() - start_time
            self.insaits.send_message(
                text=f"[Crew Completed] Duration: {elapsed:.1f}s",
                sender_id="crew_manager",
                receiver_id="output",
                llm_id="system"
            )

            return result

        finally:
            # Restore original methods
            for agent in crew.agents:
                agent_name = getattr(agent, 'name', None) or getattr(agent, 'role', 'unknown')
                if agent_name in original_executes:
                    agent.execute_task = original_executes[agent_name]

    def wrap_agent(self, agent: Any) -> Any:
        """
        Wrap a single CrewAI Agent with monitoring.

        Useful when you want to monitor specific agents
        without wrapping the entire crew.

        Args:
            agent: CrewAI Agent instance

        Returns:
            The same agent with monitoring enabled
        """
        agent_name = getattr(agent, 'name', None) or getattr(agent, 'role', 'unknown')
        llm_name = self._extract_llm_name(agent)
        self.insaits.register_agent(agent_name, llm_name)

        if hasattr(agent, 'execute_task'):
            original_execute = agent.execute_task

            @wraps(original_execute)
            def monitored_execute(task, *args, **kwargs):
                # Log task
                task_desc = getattr(task, 'description', str(task))[:200]
                self.insaits.send_message(
                    text=f"[Executing] {task_desc}",
                    sender_id="task_manager",
                    receiver_id=agent_name,
                    llm_id="system"
                )

                result = original_execute(task, *args, **kwargs)

                # Log result
                result_text = str(result)[:500] if result else "No output"
                msg_result = self.insaits.send_message(
                    text=result_text,
                    sender_id=agent_name,
                    receiver_id="task_manager",
                    llm_id=llm_name
                )

                if msg_result.get("anomalies"):
                    self._anomalies.extend(msg_result["anomalies"])

                return result

            agent.execute_task = monitored_execute

        return agent

    def get_anomalies(self) -> List[Dict]:
        """Get all anomalies detected during crew execution."""
        return self._anomalies.copy()

    def get_stats(self) -> Dict:
        """Get monitoring statistics."""
        return self.insaits.get_stats()

    def get_conversation(self, limit: int = 100) -> List[Dict]:
        """Get full conversation history."""
        return self.insaits.get_conversation(limit=limit)

    def analyze_crew_health(self) -> Dict:
        """
        Analyze overall health of crew communications.

        Returns:
            Dictionary with health metrics including:
            - overall_health: 'good', 'warning', or 'poor'
            - anomaly_count: Total anomalies detected
            - agent_stats: Per-agent statistics
            - recommendations: Suggested improvements
        """
        stats = self.insaits.get_stats()
        discussions = self.insaits.get_all_discussions()

        # Calculate metrics
        total_anomalies = len(self._anomalies)
        total_messages = stats.get('total_messages', 0)
        anomaly_rate = total_anomalies / max(total_messages, 1)

        # Determine health
        if anomaly_rate < 0.1:
            health = 'good'
        elif anomaly_rate < 0.3:
            health = 'warning'
        else:
            health = 'poor'

        # Generate recommendations
        recommendations = []
        if total_anomalies > 0:
            # Analyze anomaly types
            anomaly_types = {}
            for a in self._anomalies:
                atype = a.get('type', 'unknown')
                anomaly_types[atype] = anomaly_types.get(atype, 0) + 1

            if anomaly_types.get('CONTEXT_LOSS', 0) > 2:
                recommendations.append(
                    "Context loss detected - consider adding more context in agent prompts"
                )
            if anomaly_types.get('CROSS_LLM_JARGON', 0) > 2:
                recommendations.append(
                    "Jargon detected - ensure agents use consistent terminology"
                )
            if anomaly_types.get('SHORTHAND_EMERGENCE', 0) > 2:
                recommendations.append(
                    "Shorthand emerging - agents may be oversimplifying responses"
                )

        return {
            'overall_health': health,
            'anomaly_count': total_anomalies,
            'anomaly_rate': round(anomaly_rate, 3),
            'total_messages': total_messages,
            'agent_count': len(stats.get('agents', [])),
            'discussions': discussions,
            'recommendations': recommendations
        }

    def export_log(self, filepath: str) -> str:
        """Export conversation log to file."""
        return self.insaits.export_conversation_log(filepath)


def monitor_crew(
    crew: Any,
    api_key: Optional[str] = None,
    session_name: Optional[str] = None
) -> tuple:
    """
    Convenience function to quickly monitor a CrewAI crew.

    Args:
        crew: CrewAI Crew to monitor
        api_key: Optional InsAIts API key
        session_name: Optional session name

    Returns:
        Tuple of (monitored_crew, monitor_instance)

    Example:
        crew, monitor = monitor_crew(my_crew, session_name="marketing_crew")
        result = crew.kickoff()
        print(monitor.analyze_crew_health())
    """
    monitor = CrewAIMonitor(api_key=api_key, session_name=session_name)
    monitored = monitor.wrap_crew(crew)
    return monitored, monitor
