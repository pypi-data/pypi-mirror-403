import uuid
import time
import threading
import logging
import json
import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime

from .detector import AnomalyDetector, Anomaly
from .embeddings import get_synthetic_embedding, get_local_embedding, cache
from .exceptions import RateLimitError, insAItsError
from .license import LicenseManager
from .config import (
    ANONYMOUS_LIMITS,
    get_tier_limits,
    get_feature,
    PRICING_URL,
    REGISTER_URL,
)

# New: LLM integration for decipher
try:
    from .local_llm import ollama_chat
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

try:
    import websocket
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

try:
    import networkx as nx
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False

logger = logging.getLogger(__name__)

class insAItsMonitor:
    """Main SDK class - Multi-LLM deciphering + prevention"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        cloud_url: str = "wss://api.insa-its.com/ws",
        auto_prevent: bool = True,
        decipher_mode: bool = True,
        session_name: Optional[str] = None,
        use_cloud_embeddings: bool = False,  # Disabled by default - use local for speed
        cloud_timeout: int = 30,  # Timeout for cloud requests (seconds)
        cloud_retries: int = 2  # Number of retries for cloud
    ):
        self.api_key = api_key
        self.cloud_url = cloud_url
        self.session_id = str(uuid.uuid4())
        self.session_name = session_name or f"session-{datetime.now().isoformat()}"

        # Cloud embedding settings
        self.use_cloud_embeddings = use_cloud_embeddings
        self.cloud_timeout = cloud_timeout
        self.cloud_retries = cloud_retries

        # License management - ALWAYS validate (even without key)
        self.license = LicenseManager(api_key)
        validation = self.license.validate()
        logger.info(f"License validation: {validation}")

        # Tier-based access
        self.tier = self.license.tier
        self._limits = get_tier_limits(self.tier)
        self.is_pro = self.tier in ("pro", "lifetime", "enterprise")
        self.is_paid = self.tier in ("starter", "pro", "lifetime", "enterprise")
        self.auto_prevent = auto_prevent and self.is_pro
        self.decipher_mode = decipher_mode and get_feature(self.tier, "integrations")

        # History: {agent_id: {llm_id: List[msg]}}
        self.history: Dict[str, Dict[str, List[Dict]]] = {}
        self.agents: List[str] = []

        # Rate limiting
        self.last_msg_time: Dict[str, float] = {}

        # Usage tracking
        self.session_message_count = 0
        self.max_messages = self._limits.get("session_messages", 5)

        # Components
        self.detector = AnomalyDetector()

        # Anomaly tracking for trend analysis
        self.anomaly_history: List[Dict] = []

        # Graph - only for registered users
        if GRAPH_AVAILABLE and get_feature(self.tier, "graph"):
            self.graph = nx.DiGraph()
        else:
            self.graph = None

        # Cloud
        self.ws = None
        self.ws_thread = None
        if self.is_pro and WS_AVAILABLE:
            threading.Thread(target=self._connect_with_retry, daemon=True).start()

    def _connect_with_retry(self):
        max_retries = 10
        for attempt in range(max_retries):
            try:
                def on_open(ws):
                    ws.send(json.dumps({
                        "type": "auth",
                        "session_id": self.session_id,
                        "api_key": self.api_key
                    }))

                def on_message(ws, msg):
                    data = json.loads(msg)
                    if data.get("anomalies"):
                        logger.info(f"Cloud anomalies: {data['anomalies']}")

                self.ws = websocket.WebSocketApp(
                    self.cloud_url,
                    on_open=on_open,
                    on_message=on_message
                )
                self.ws.run_forever(ping_interval=30)
            except Exception as e:
                logger.error(f"WS attempt {attempt+1} failed: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

    def register_agent(self, agent_id: str, llm_id: str = "unknown"):
        if agent_id not in self.agents:
            self.agents.append(agent_id)
            self.history[agent_id] = {}
        if llm_id not in self.history[agent_id]:
            self.history[agent_id][llm_id] = []
        if self.graph:
            self.graph.add_node(f"{agent_id}:{llm_id}")

    def send_message(
        self,
        text: str,
        sender_id: str,
        receiver_id: Optional[str] = None,
        llm_id: str = "unknown"
    ) -> Dict[str, Any]:
        # Check usage quota based on tier
        if self.max_messages != -1:  # -1 = unlimited
            if self.session_message_count >= self.max_messages:
                if self.tier == "anonymous":
                    msg = f"Anonymous limit ({self.max_messages} messages) reached. Get FREE API key for 100 messages!"
                else:
                    msg = f"Message limit ({self.max_messages}) reached. Upgrade for more."
                return {
                    "error": "limit_reached",
                    "message": msg,
                    "upgrade_url": PRICING_URL,
                    "register_url": REGISTER_URL,
                    "anomalies": [],
                    "remaining": 0,
                    "tier": self.tier
                }

        # Rate limit
        now = time.time()
        if now - self.last_msg_time.get(sender_id, 0) < 0.1:
            raise RateLimitError("Rate limit: max 10 msg/sec per agent")
        self.last_msg_time[sender_id] = now

        self.register_agent(sender_id, llm_id)
        if receiver_id:
            self.register_agent(receiver_id, llm_id)

        # Track usage
        self.session_message_count += 1
        self.license.track_usage(message_count=1)

        # Embedding - try cloud if enabled and Pro, always fallback to local
        embedding = None
        if self.is_pro and self.use_cloud_embeddings:
            embedding = self.license.get_cloud_embedding(
                text,
                timeout=self.cloud_timeout,
                max_retries=self.cloud_retries
            )
        if embedding is None:
            # Local embeddings (sentence-transformers or synthetic fallback)
            embedding = get_local_embedding(text)

        msg = {
            "text": text,
            "embedding": embedding,
            "sender": sender_id,
            "receiver": receiver_id,
            "llm_id": llm_id,
            "word_count": len(text.split()),
            "timestamp": now,
            "message_id": str(uuid.uuid4())
        }

        self.history[sender_id][llm_id].append(msg)
        if len(self.history[sender_id][llm_id]) > 100:
            self.history[sender_id][llm_id].pop(0)

        anomalies = self.detector.detect(msg, self.history, sender_id, llm_id, receiver_id)

        # Track anomalies for trend analysis
        for anomaly in anomalies:
            self.anomaly_history.append({
                "type": anomaly.type,
                "severity": anomaly.severity,
                "llm_id": anomaly.llm_id,
                "agent_id": anomaly.agent_id,
                "details": anomaly.details,
                "timestamp": anomaly.timestamp,
                "message_id": msg["message_id"]
            })

        # Calculate remaining messages
        if self.max_messages == -1:
            remaining = -1  # Unlimited
        else:
            remaining = max(0, self.max_messages - self.session_message_count)

        result = {
            "anomalies": [a.__dict__ for a in anomalies],
            "message": msg,
            "remaining": remaining,
            "tier": self.tier
        }

        # Show warning for anonymous users
        if self.tier == "anonymous" and remaining <= 2 and remaining > 0:
            print(f"\n[InsAIts] Warning: Only {remaining} messages left! Get FREE key: {REGISTER_URL}\n")

        if anomalies and self.decipher_mode:
            result["decipher_prompt"] = self._generate_decipher(anomalies)

        # Real graph similarity calculation
        if receiver_id and self.graph:
            similarity = self._calculate_edge_similarity(sender_id, receiver_id, llm_id, embedding)
            self.graph.add_edge(
                f"{sender_id}:{llm_id}",
                f"{receiver_id}:{llm_id}",
                similarity=round(similarity, 4),
                drift=round(1 - similarity, 4),
                last_update=now
            )

        return result

    def _calculate_edge_similarity(
        self,
        sender_id: str,
        receiver_id: str,
        llm_id: str,
        current_embedding: np.ndarray
    ) -> float:
        """Calculate real similarity between sender and receiver communication patterns"""
        recv_hist = self.history.get(receiver_id, {})

        # Get receiver's recent messages
        similarities = []
        for recv_llm, msgs in recv_hist.items():
            if msgs:
                for msg in msgs[-5:]:  # Last 5 messages
                    recv_emb = np.array(msg["embedding"])
                    sim = float(np.dot(current_embedding, recv_emb) /
                               (np.linalg.norm(current_embedding) * np.linalg.norm(recv_emb) + 1e-8))
                    similarities.append(sim)

        if similarities:
            return sum(similarities) / len(similarities)
        return 0.5  # Neutral if no history

    def _generate_decipher(self, anomalies: List[Anomaly]) -> str:
        lines = ["Clarify for cross-LLM understanding:"]
        for a in anomalies:
            if a.type == "CROSS_LLM_SHORTHAND":
                lines.append("- Expand shorthand across models")
            elif a.type == "CROSS_LLM_JARGON":
                lines.append(f"- Define: {', '.join(a.details.get('new_terms', []))}")
        return "\n".join(lines)

    def decipher(
        self,
        msg: Dict,
        target_llm_id: Optional[str] = None,
        model: str = "phi3"
    ) -> Dict[str, Any]:
        """
        The killer feature: uses local Phi-3 to expand shorthand, explain jargon,
        remove hedges, and rephrase for target LLM style.
        Returns structured deciphered output.
        """
        if not LLM_AVAILABLE:
            return {
                "error": "Ollama integration not available",
                "original_text": msg["text"]
            }

        # Quick check if Ollama is reachable
        test_resp = ollama_chat([{"role": "user", "content": "ping"}], model=model)
        if test_resp is None:
            return {
                "error": "Ollama not available (run 'ollama serve' and 'ollama pull phi3')",
                "original_text": msg["text"]
            }

        # Build conversation context (last 15 exchanges)
        receiver = msg.get("receiver")
        if receiver:
            thread = self.get_conversation_thread(msg["sender"], receiver, limit=15)
        else:
            # Fallback: recent messages from sender
            recent = []
            for llm_hist in self.history.get(msg["sender"], {}).values():
                recent.extend(llm_hist[-10:])
            thread = sorted(recent, key=lambda x: x["timestamp"])[-15:]

        context_lines = []
        prior_thread = thread[:-1] if thread else []
        if prior_thread:
            for m in prior_thread:
                direction = f"{m['sender']} → {m.get('receiver', 'unknown')}"
                context_lines.append(f"{direction} ({m['llm_id']}): {m['text']}")

        context_str = "\n".join(context_lines) if context_lines else "No prior context available."

        current_text = msg["text"]
        target_style = target_llm_id or "clear, detailed, and confident"

        system_prompt = (
            "You are an AI-to-AI communication mediator. "
            "Expand shorthand, explain undefined jargon, remove hedging for higher confidence, "
            "and rephrase for compatibility with the target LLM style."
        )

        user_prompt = f"""Conversation context:
{context_str}

Latest message:
{current_text}

Target LLM style: {target_style}

Tasks:
- Expand any shorthand/abbreviations
- Explain any new or unclear acronyms/terms
- Increase confidence (remove hedges like 'maybe', 'perhaps')
- Rephrase if needed for the target style

Output ONLY valid JSON:
{{
  "expanded_text": "full clear version",
  "explanations": {{"TERM1": "meaning", "TERM2": "meaning"}} or {{}},
  "rephrased_text": "version optimized for target LLM (or same as expanded if no change)",
  "confidence_improved": true | false
}}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = ollama_chat(messages, model=model, temperature=0.4)
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"raw_llm_response": response, "original_text": current_text}

        return {"error": "No response from LLM", "original_text": current_text}

    def get_conversation_thread(
        self,
        agent_a: str,
        agent_b: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get the conversation thread between two specific agents.
        Returns messages in chronological order showing the back-and-forth.
        """
        thread = []

        # Collect messages from agent_a to agent_b
        for llm, msgs in self.history.get(agent_a, {}).items():
            for m in msgs:
                if m.get("receiver") == agent_b:
                    thread.append({**m, "_direction": f"{agent_a} → {agent_b}"})

        # Collect messages from agent_b to agent_a
        for llm, msgs in self.history.get(agent_b, {}).items():
            for m in msgs:
                if m.get("receiver") == agent_a:
                    thread.append({**m, "_direction": f"{agent_b} → {agent_a}"})

        # Sort chronologically
        thread = sorted(thread, key=lambda x: x["timestamp"])[-limit:]

        return thread

    def export_graph(self) -> Dict:
        if not self.graph:
            return {}
        data = nx.node_link_data(self.graph)
        for link in data["links"]:
            link["drift"] = 1 - link.get("similarity", 1)
        return data

    def get_stats(self) -> Dict:
        total_messages = sum(len(h) for a in self.history.values() for h in a.values())

        if self.is_pro:
            remaining = -1
        else:
            remaining = max(0, self.max_messages - self.session_message_count)

        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "agents": self.agents,
            "total_messages": total_messages,
            "session_messages": self.session_message_count,
            "remaining": remaining,
            "limit": self.max_messages if not self.is_pro else -1,
            "tier": self.license.tier,
            "is_pro": self.is_pro,
            "license_status": self.license.get_status(),
            "llm_decipher_available": LLM_AVAILABLE
        }

    # ============================================
    # CONVERSATION READING & ANALYSIS
    # ============================================

    def get_conversation(
        self,
        agent_id: Optional[str] = None,
        llm_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Read conversation history.
        - If agent_id provided: get that agent's messages
        - If llm_id provided: filter by LLM
        - If neither: get all messages chronologically
        """
        messages = []

        if agent_id and agent_id in self.history:
            agent_hist = self.history[agent_id]
            if llm_id and llm_id in agent_hist:
                messages = agent_hist[llm_id][-limit:]
            else:
                for llm, msgs in agent_hist.items():
                    messages.extend(msgs)
        else:
            # All messages from all agents
            for aid, agent_hist in self.history.items():
                for llm, msgs in agent_hist.items():
                    messages.extend(msgs)

        # Sort by timestamp and limit
        messages = sorted(messages, key=lambda x: x["timestamp"])[-limit:]

        # Return readable format (without embeddings for readability)
        return [{
            "message_id": m.get("message_id", "N/A"),
            "text": m["text"],
            "sender": m["sender"],
            "receiver": m.get("receiver"),
            "llm_id": m["llm_id"],
            "word_count": m["word_count"],
            "timestamp": m["timestamp"],
            "time_formatted": datetime.fromtimestamp(m["timestamp"]).strftime("%H:%M:%S")
        } for m in messages]

    def get_discussion_thread(
        self,
        agent_a: str,
        agent_b: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get the conversation thread between two specific agents.
        Returns messages in chronological order showing the back-and-forth.
        """
        thread = self.get_conversation_thread(agent_a, agent_b, limit)

        return [{
            "direction": m["_direction"],
            "text": m["text"],
            "llm_id": m["llm_id"],
            "word_count": m["word_count"],
            "time": datetime.fromtimestamp(m["timestamp"]).strftime("%H:%M:%S")
        } for m in thread]

    def analyze_discussion(
        self,
        agent_a: str,
        agent_b: str
    ) -> Dict:
        """
        Analyze the quality of discussion between two agents.
        Returns semantic coherence, drift patterns, and communication health.
        """
        thread = self.get_conversation_thread(agent_a, agent_b, limit=1000)

        if len(thread) < 2:
            return {"status": "insufficient_data", "message_count": len(thread)}

        # Calculate sequential similarity (coherence)
        similarities = []
        for i in range(1, len(thread)):
            emb_a = np.array(thread[i-1]["embedding"])
            emb_b = np.array(thread[i]["embedding"])
            sim = float(np.dot(emb_a, emb_b) /
                       (np.linalg.norm(emb_a) * np.linalg.norm(emb_b) + 1e-8))
            similarities.append(sim)

        avg_coherence = sum(similarities) / len(similarities) if similarities else 0

        # Detect drift (declining similarity over time)
        drift_detected = False
        if len(similarities) >= 4:
            first_half = sum(similarities[:len(similarities)//2]) / (len(similarities)//2)
            second_half = sum(similarities[len(similarities)//2:]) / (len(similarities) - len(similarities)//2)
            drift_detected = (first_half - second_half) > 0.15

        # Word count analysis (shorthand emergence)
        word_counts = [m["word_count"] for m in thread]
        avg_words_start = sum(word_counts[:3]) / min(3, len(word_counts))
        avg_words_end = sum(word_counts[-3:]) / min(3, len(word_counts))
        compression_trend = avg_words_start / max(avg_words_end, 1)

        return {
            "message_count": len(thread),
            "avg_coherence": round(avg_coherence, 3),
            "coherence_health": "good" if avg_coherence > 0.6 else "warning" if avg_coherence > 0.4 else "poor",
            "drift_detected": drift_detected,
            "compression_ratio": round(compression_trend, 2),
            "shorthand_risk": compression_trend > 2.0,
            "similarity_trend": similarities[-5:] if len(similarities) >= 5 else similarities
        }

    def get_all_discussions(self) -> List[Dict]:
        """
        Get summary of all agent-to-agent discussion pairs.
        """
        pairs = set()

        for agent_id, agent_hist in self.history.items():
            for llm, msgs in agent_hist.items():
                for m in msgs:
                    if m.get("receiver"):
                        pair = tuple(sorted([agent_id, m["receiver"]]))
                        pairs.add(pair)

        discussions = []
        for agent_a, agent_b in pairs:
            analysis = self.analyze_discussion(agent_a, agent_b)
            discussions.append({
                "agents": f"{agent_a} <-> {agent_b}",
                "message_count": analysis.get("message_count", 0),
                "health": analysis.get("coherence_health", "unknown"),
                "drift": analysis.get("drift_detected", False)
            })

        return sorted(discussions, key=lambda x: x["message_count"], reverse=True)

    def export_conversation_log(
        self,
        filepath: Optional[str] = None
    ) -> str:
        """
        Export full conversation log as formatted text.
        """
        lines = [
            f"=== InsAIts Session Log ===",
            f"Session: {self.session_name}",
            f"ID: {self.session_id}",
            f"Agents: {', '.join(self.agents)}",
            f"{'='*40}",
            ""
        ]

        all_msgs = []
        for agent_id, agent_hist in self.history.items():
            for llm, msgs in agent_hist.items():
                all_msgs.extend(msgs)

        all_msgs = sorted(all_msgs, key=lambda x: x["timestamp"])

        for m in all_msgs:
            time_str = datetime.fromtimestamp(m["timestamp"]).strftime("%H:%M:%S")
            receiver = f" → {m['receiver']}" if m.get("receiver") else ""
            lines.append(f"[{time_str}] {m['sender']}{receiver} ({m['llm_id']}):")
            lines.append(f"  {m['text']}")
            lines.append("")

        log_text = "\n".join(lines)

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(log_text)

        return log_text

    # ============================================
    # ADAPTIVE LEARNING & TREND ANALYSIS
    # ============================================

    def learn_from_session(
        self,
        min_occurrences: int = 3,
        auto_save: bool = True
    ) -> Dict:
        """
        Analyze session messages and learn new jargon terms.

        This method extracts acronyms/terms from all session messages,
        identifies frequently used ones, and adds them to the learned dictionary.

        Args:
            min_occurrences: Minimum times a term must appear to be learned
            auto_save: Whether to persist the dictionary after learning

        Returns:
            Dict with learning statistics
        """
        import re
        from collections import Counter

        # Collect all text from session
        all_text = []
        for agent_hist in self.history.values():
            for llm_msgs in agent_hist.values():
                for msg in llm_msgs:
                    all_text.append(msg["text"])

        if not all_text:
            return {
                "status": "no_data",
                "message": "No messages in session to learn from",
                "terms_learned": 0
            }

        # Extract all acronyms
        full_text = " ".join(all_text)
        acronyms = re.findall(r'\b[A-Z]{2,}\b', full_text)
        term_counts = Counter(acronyms)

        # Filter: only learn terms that appear frequently and aren't known
        new_terms = []
        skipped_known = []
        skipped_low_count = []

        for term, count in term_counts.items():
            if self.detector._is_known_term(term):
                skipped_known.append(term)
            elif count < min_occurrences:
                skipped_low_count.append((term, count))
            else:
                # Learn this term
                self.detector.add_learned_term(term)
                new_terms.append((term, count))

        # Optionally save
        if auto_save and new_terms:
            self.detector._save_dict()

        return {
            "status": "success",
            "terms_learned": len(new_terms),
            "learned_terms": new_terms,
            "already_known": len(skipped_known),
            "below_threshold": len(skipped_low_count),
            "jargon_stats": self.detector.get_jargon_stats()
        }

    def get_anomaly_trends(
        self,
        window_minutes: int = 5,
        include_details: bool = False
    ) -> Dict:
        """
        Analyze anomaly patterns over time.

        Provides insights into:
        - Anomaly frequency and distribution
        - Severity trends
        - Type breakdown
        - Time-based patterns

        Args:
            window_minutes: Time window for grouping anomalies
            include_details: Whether to include full anomaly details

        Returns:
            Dict with trend analysis
        """
        if not self.anomaly_history:
            return {
                "status": "no_anomalies",
                "message": "No anomalies detected in this session",
                "total_count": 0
            }

        from collections import Counter

        now = time.time()

        # Basic counts
        type_counts = Counter(a["type"] for a in self.anomaly_history)
        severity_counts = Counter(a["severity"] for a in self.anomaly_history)
        agent_counts = Counter(a["agent_id"] for a in self.anomaly_history)
        llm_counts = Counter(a["llm_id"] for a in self.anomaly_history)

        # Time-based analysis
        window_seconds = window_minutes * 60
        time_windows = {}

        for anomaly in self.anomaly_history:
            # Calculate which window this anomaly falls into
            age_seconds = now - anomaly["timestamp"]
            window_index = int(age_seconds // window_seconds)
            window_label = f"{window_index * window_minutes}-{(window_index + 1) * window_minutes}min ago"

            if window_label not in time_windows:
                time_windows[window_label] = []
            time_windows[window_label].append(anomaly["type"])

        # Calculate trend (increasing/decreasing)
        if len(self.anomaly_history) >= 4:
            mid = len(self.anomaly_history) // 2
            first_half_count = mid
            second_half_count = len(self.anomaly_history) - mid
            trend = "increasing" if second_half_count > first_half_count * 1.2 else \
                    "decreasing" if first_half_count > second_half_count * 1.2 else "stable"
        else:
            trend = "insufficient_data"

        # Build result
        result = {
            "status": "success",
            "total_count": len(self.anomaly_history),
            "by_type": dict(type_counts),
            "by_severity": dict(severity_counts),
            "by_agent": dict(agent_counts),
            "by_llm": dict(llm_counts),
            "trend": trend,
            "time_distribution": {
                k: {"count": len(v), "types": dict(Counter(v))}
                for k, v in sorted(time_windows.items())
            },
            "most_common_type": type_counts.most_common(1)[0] if type_counts else None,
            "high_severity_count": severity_counts.get("high", 0),
            "session_health": self._calculate_session_health(type_counts, severity_counts)
        }

        if include_details:
            result["anomaly_history"] = self.anomaly_history

        return result

    def _calculate_session_health(
        self,
        type_counts: 'Counter',
        severity_counts: 'Counter'
    ) -> Dict:
        """
        Calculate overall session health based on anomaly patterns.

        Returns health score (0-100) and status.
        """
        total = sum(type_counts.values())

        if total == 0:
            return {"score": 100, "status": "excellent", "message": "No anomalies detected"}

        # Deduct points based on severity
        high_penalty = severity_counts.get("high", 0) * 15
        medium_penalty = severity_counts.get("medium", 0) * 5
        low_penalty = severity_counts.get("low", 0) * 2

        # Extra penalty for certain anomaly types
        context_loss_penalty = type_counts.get("CONTEXT_LOSS", 0) * 10
        shorthand_penalty = type_counts.get("SHORTHAND_EMERGENCE", 0) * 5

        total_penalty = min(100, high_penalty + medium_penalty + low_penalty +
                          context_loss_penalty + shorthand_penalty)
        score = max(0, 100 - total_penalty)

        if score >= 80:
            status, message = "good", "Communication is healthy with minor issues"
        elif score >= 60:
            status, message = "warning", "Some communication issues detected"
        elif score >= 40:
            status, message = "concerning", "Significant communication issues"
        else:
            status, message = "critical", "Severe communication breakdown detected"

        return {
            "score": score,
            "status": status,
            "message": message,
            "factors": {
                "high_severity_anomalies": severity_counts.get("high", 0),
                "context_losses": type_counts.get("CONTEXT_LOSS", 0),
                "shorthand_emergences": type_counts.get("SHORTHAND_EMERGENCE", 0)
            }
        }

    def get_jargon_dictionary(self) -> Dict:
        """
        Get the current state of the adaptive jargon dictionary.

        Returns statistics and the learned/candidate terms.
        """
        return self.detector.get_jargon_stats()

    def add_jargon_term(self, term: str, meaning: Optional[str] = None) -> None:
        """
        Manually add a term to the jargon dictionary.

        Args:
            term: The acronym/term to add (will be uppercased)
            meaning: Optional expanded meaning
        """
        self.detector.add_learned_term(term, meaning)
        logger.info(f"Manually added jargon term: {term.upper()}")