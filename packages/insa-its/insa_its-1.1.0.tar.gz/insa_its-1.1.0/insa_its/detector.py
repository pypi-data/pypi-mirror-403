import numpy as np
import re
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

# New: LLM integration
try:
    from .local_llm import ollama_chat
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

# Default cache directory
INSAITS_CACHE_DIR = Path.home() / ".insaits"
JARGON_FILE = INSAITS_CACHE_DIR / "jargon.json"

@dataclass
class Anomaly:
    type: str
    severity: str
    llm_id: str
    agent_id: str
    details: Dict
    timestamp: float

class AnomalyDetector:
    """Multi-LLM statistical anomaly detection with adaptive jargon learning"""

    # Promotion threshold: how many times a term must appear before auto-learning
    CANDIDATE_PROMOTION_THRESHOLD = 5
    # Maximum candidates to track (prevents memory bloat)
    MAX_CANDIDATES = 500

    def __init__(self, auto_learn: bool = True):
        """
        Initialize detector with adaptive jargon dictionary.

        Args:
            auto_learn: If True, automatically learn new terms from conversations
        """
        self.auto_learn = auto_learn

        # Adaptive jargon dictionary
        # - known: seed terms (common acronyms we ship with)
        # - candidate: {term: count} - terms seen but not yet promoted
        # - learned: terms auto-promoted after threshold
        # - expanded: {term: "full meaning"} - from LLM decipher (optional)
        self.jargon_dict: Dict[str, any] = {
            "known": self._get_seed_terms(),
            "candidate": defaultdict(int),
            "learned": set(),
            "expanded": {}
        }

        # Load persisted dictionary
        self._load_dict()

        # LLM fingerprint patterns - typical response characteristics
        self.llm_patterns = {
            # OpenAI models
            'gpt-4': {'avg_words': 40, 'jargon_heavy': False},
            'gpt-4o': {'avg_words': 35, 'jargon_heavy': False},
            'gpt-4o-mini': {'avg_words': 30, 'jargon_heavy': False},
            'gpt-3.5-turbo': {'avg_words': 25, 'jargon_heavy': False},
            # Anthropic models
            'claude-3': {'avg_words': 50, 'jargon_heavy': False},
            'claude-3.5': {'avg_words': 45, 'jargon_heavy': False},
            'claude-3-opus': {'avg_words': 60, 'jargon_heavy': False},
            'claude-3-sonnet': {'avg_words': 45, 'jargon_heavy': False},
            'claude-3-haiku': {'avg_words': 30, 'jargon_heavy': False},
            # Google models
            'gemini-2.0': {'avg_words': 40, 'jargon_heavy': True},
            'gemini-1.5-pro': {'avg_words': 45, 'jargon_heavy': True},
            'gemini-1.5-flash': {'avg_words': 30, 'jargon_heavy': True},
            # xAI
            'grok-2': {'avg_words': 35, 'jargon_heavy': False},
            # Open source
            'llama-3.1': {'avg_words': 35, 'jargon_heavy': True},
            'llama-3.2': {'avg_words': 30, 'jargon_heavy': True},
            'mistral': {'avg_words': 30, 'jargon_heavy': True},
            'phi3': {'avg_words': 25, 'jargon_heavy': False},
        }

    def _get_seed_terms(self) -> Set[str]:
        """Return the seed set of common acronyms to avoid false positives."""
        return {
            # AI/ML
            'AI', 'ML', 'NLP', 'LLM', 'GPT', 'CNN', 'RNN', 'GAN', 'RAG', 'AGI',
            'BERT', 'LSTM', 'DNN', 'SVM', 'KNN', 'PCA', 'RLHF', 'DPO', 'PPO',
            # Web/API
            'API', 'URL', 'HTTP', 'HTTPS', 'REST', 'JSON', 'XML', 'HTML', 'CSS',
            'JS', 'TS', 'SQL', 'DOM', 'CDN', 'SDK', 'CLI', 'GUI', 'URI', 'JWT',
            'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'CORS',
            # Infrastructure
            'AWS', 'GCP', 'CPU', 'GPU', 'RAM', 'SSD', 'VM', 'DNS', 'IP', 'SSL',
            'TLS', 'SSH', 'FTP', 'TCP', 'UDP', 'VPN', 'LAN', 'WAN', 'NAS', 'SAN',
            'K8S', 'EC2', 'S3', 'RDS', 'ECS', 'EKS', 'IAM', 'VPC', 'ALB', 'ELB',
            # Business/Common
            'ID', 'OK', 'ETA', 'FYI', 'TBD', 'FAQ', 'KPI', 'ROI', 'SLA', 'EOD',
            'ASAP', 'CEO', 'CTO', 'CFO', 'COO', 'HR', 'PR', 'QA', 'PM', 'UI', 'UX',
            'MVP', 'POC', 'RFP', 'RFQ', 'NDA', 'SOW', 'MOU', 'LOI',
            # E-commerce/Customer Service
            'SKU', 'RMA', 'PO', 'ERP', 'CRM', 'B2B', 'B2C', 'D2C', 'POS', 'WMS',
            # Marketing/Advertising
            'SEO', 'SEM', 'PPC', 'CTR', 'CVR', 'CPA', 'CPM', 'CPC', 'ROAS',
            'CAC', 'CLV', 'LTV', 'AOV', 'GMV', 'CRO', 'ABM', 'UGC', 'SMM',
            # Programming
            'OOP', 'CRUD', 'IDE', 'GIT', 'CI', 'CD', 'TDD', 'BDD', 'DRY', 'SOLID',
            'MVC', 'MVP', 'MVVM', 'ORM', 'DSL', 'AST', 'JIT', 'AOT', 'GC',
            # Data/Files
            'CSV', 'PDF', 'PNG', 'JPG', 'GIF', 'MP4', 'ZIP', 'TAR', 'YAML', 'TOML',
            # Metrics
            'NPS', 'CSAT', 'MRR', 'ARR', 'DAU', 'MAU', 'WAU', 'ARPU', 'ARPPU',
            # Finance
            'USD', 'EUR', 'GBP', 'JPY', 'BTC', 'ETH', 'IPO', 'ICO', 'VC', 'PE',
            'EBITDA', 'P&L', 'CFO', 'GAAP', 'IFRS', 'AML', 'KYC',
            # Healthcare
            'HIPAA', 'PHI', 'EHR', 'EMR', 'FDA', 'CDC', 'WHO', 'ICU', 'ER',
            # Legal
            'GDPR', 'CCPA', 'SOC', 'PCI', 'DSS', 'ISO', 'NIST', 'FERPA',
        }

    def _load_dict(self) -> None:
        """Load persisted jargon dictionary from disk."""
        try:
            if JARGON_FILE.exists():
                with open(JARGON_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Merge loaded data with seed (seed always takes priority)
                if "learned" in data:
                    self.jargon_dict["learned"] = set(data["learned"])
                if "candidate" in data:
                    self.jargon_dict["candidate"] = defaultdict(int, data["candidate"])
                if "expanded" in data:
                    self.jargon_dict["expanded"] = data["expanded"]

                logger.info(f"Loaded jargon dictionary: {len(self.jargon_dict['learned'])} learned terms")
        except Exception as e:
            logger.warning(f"Could not load jargon dictionary: {e}")

    def _save_dict(self) -> None:
        """Persist jargon dictionary to disk."""
        try:
            # Create directory if needed
            INSAITS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

            # Prepare data for JSON serialization
            data = {
                "learned": list(self.jargon_dict["learned"]),
                "candidate": dict(self.jargon_dict["candidate"]),
                "expanded": self.jargon_dict["expanded"],
                "last_updated": time.time()
            }

            with open(JARGON_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved jargon dictionary: {len(self.jargon_dict['learned'])} learned terms")
        except Exception as e:
            logger.error(f"Could not save jargon dictionary: {e}", exc_info=True)

    def _is_known_term(self, term: str) -> bool:
        """Check if a term is known (seed or learned)."""
        upper = term.upper()
        return (
            upper in self.jargon_dict["known"] or
            upper in self.jargon_dict["learned"]
        )

    def _track_candidate(self, term: str) -> bool:
        """
        Track a candidate term and promote if threshold reached.
        Returns True if the term was promoted to learned.
        """
        if not self.auto_learn:
            return False

        upper = term.upper()

        # Skip if already known
        if self._is_known_term(upper):
            return False

        # Increment count
        self.jargon_dict["candidate"][upper] += 1

        # Check for promotion
        if self.jargon_dict["candidate"][upper] >= self.CANDIDATE_PROMOTION_THRESHOLD:
            self.jargon_dict["learned"].add(upper)
            del self.jargon_dict["candidate"][upper]
            logger.info(f"Auto-learned new term: {upper}")
            self._save_dict()
            return True

        # Cleanup: remove oldest candidates if too many
        if len(self.jargon_dict["candidate"]) > self.MAX_CANDIDATES:
            # Remove terms with lowest counts
            sorted_candidates = sorted(
                self.jargon_dict["candidate"].items(),
                key=lambda x: x[1]
            )
            for term_to_remove, _ in sorted_candidates[:100]:
                del self.jargon_dict["candidate"][term_to_remove]

        return False

    def add_learned_term(self, term: str, expanded: Optional[str] = None) -> None:
        """Manually add a term to the learned dictionary."""
        upper = term.upper()
        self.jargon_dict["learned"].add(upper)
        if expanded:
            self.jargon_dict["expanded"][upper] = expanded
        self._save_dict()
        logger.info(f"Manually added term: {upper}")

    def get_jargon_stats(self) -> Dict:
        """Return statistics about the jargon dictionary."""
        return {
            "known_terms": len(self.jargon_dict["known"]),
            "learned_terms": len(self.jargon_dict["learned"]),
            "candidate_terms": len(self.jargon_dict["candidate"]),
            "expanded_terms": len(self.jargon_dict["expanded"]),
            "top_candidates": dict(
                sorted(
                    self.jargon_dict["candidate"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            )
        }

    def detect(
        self,
        current_msg: Dict,
        history: Dict[str, Dict[str, List[Dict]]],
        sender_id: str,
        llm_id: str,
        receiver_id: Optional[str] = None
    ) -> List[Anomaly]:
        anomalies = []
        agent_hist = history.get(sender_id, {})
        llm_hist = agent_hist.get(llm_id, [])

        # Always check jargon detection (doesn't need history)
        jargon = self._cross_llm_jargon(current_msg, history)
        if jargon:
            anomalies.append(jargon)

        # Always check fingerprint mismatch (doesn't need history)
        mismatch = self._fingerprint_mismatch(current_msg, llm_id)
        if mismatch:
            anomalies.append(mismatch)

        if len(llm_hist) < 2:
            if LLM_AVAILABLE:
                # Still check hedging even on first messages
                hedging = self._detect_hedging_llm(current_msg["text"])
                if hedging and hedging.get("confidence") == "Low":
                    anomalies.append(Anomaly(
                        type="LOW_CONFIDENCE",
                        severity="high",
                        llm_id=llm_id,
                        agent_id=sender_id,
                        details=hedging,
                        timestamp=time.time()
                    ))
            return anomalies
        
        prev_msg = llm_hist[-2]
        current_emb = np.array(current_msg["embedding"])
        prev_emb = np.array(prev_msg["embedding"])
        similarity = self._cosine(current_emb, prev_emb)
        
        current_words = current_msg["word_count"]
        prev_words = prev_msg["word_count"]
        
        # === Heuristic anomalies (tuned thresholds) ===

        # SHORTHAND_EMERGENCE: Detect when verbose messages suddenly become terse
        # Tuned: prev_words >= 25 (was 40), current_words <= 20 (was 15)
        # Similarity threshold lowered to 0.4 (was 0.65) - shorthand may not be semantically close
        # Also check compression ratio as backup trigger
        compression_ratio = prev_words / max(current_words, 1)
        if (prev_words >= 25 and current_words <= 20 and similarity > 0.4) or \
           (compression_ratio >= 3.0 and current_words <= 15):
            anomalies.append(Anomaly(
                type="SHORTHAND_EMERGENCE",
                severity="high",
                llm_id=llm_id,
                agent_id=sender_id,
                details={"compression_ratio": round(compression_ratio, 1), "similarity": round(similarity, 3)},
                timestamp=time.time()
            ))

        # CONTEXT_LOSS: Detect complete topic changes
        # Tuned: similarity < 0.5 (was 0.35) - real embeddings give ~0.3-0.5 for unrelated topics
        if similarity < 0.5:
            anomalies.append(Anomaly(
                type="CONTEXT_LOSS",
                severity="high",
                llm_id=llm_id,
                agent_id=sender_id,
                details={"similarity": round(similarity, 3)},
                timestamp=time.time()
            ))

        # Cross-LLM shorthand detection (receiver must exist in history)
        if receiver_id and receiver_id in history:
            cross = self._cross_llm_shorthand(current_msg, history, sender_id, llm_id, receiver_id)
            anomalies.extend(cross)

        # Note: fingerprint_mismatch and jargon are checked at the start (before early return)

        # === LLM-enhanced confirmation & new anomalies ===
        if LLM_AVAILABLE:
            # Confirm/reduce false positives on shorthand
            shorthand_anoms = [a for a in anomalies if a.type == "SHORTHAND_EMERGENCE"]
            if shorthand_anoms:
                confirm = self._confirm_shorthand_llm(prev_msg["text"], current_msg["text"])
                if confirm and confirm.get("is_shorthand"):
                    # Apply to all (though usually only one)
                    for a in shorthand_anoms:
                        a.details.update({
                            "llm_explanation": confirm.get("explanation"),
                            "llm_expanded": confirm.get("expanded")
                        })
                else:
                    # Remove all shorthand anomalies for this message
                    anomalies = [a for a in anomalies if a.type != "SHORTHAND_EMERGENCE"]

            # New: low confidence / hedging detection (few-shot style)
            hedging = self._detect_hedging_llm(current_msg["text"])
            if hedging and hedging.get("confidence") in ("Low", "Medium"):
                severity = "high" if hedging["confidence"] == "Low" else "medium"
                anomalies.append(Anomaly(
                    type="LOW_CONFIDENCE",
                    severity=severity,
                    llm_id=llm_id,
                    agent_id=sender_id,
                    details=hedging,
                    timestamp=time.time()
                ))

        return anomalies

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def _cross_llm_shorthand(self, msg: Dict, history: Dict, sender: str, sender_llm: str, receiver: str) -> List[Anomaly]:
        """Detect when short messages are semantically similar to longer ones from different LLMs."""
        anomalies = []
        recv_hist = history.get(receiver, {})
        msg_emb = np.array(msg["embedding"])
        msg_words = msg["word_count"]

        for recv_llm, msgs in recv_hist.items():
            # Only check cross-LLM communication (different LLMs)
            if recv_llm != sender_llm and msgs:
                for prev in msgs[-5:]:  # Check last 5 messages (was 3)
                    prev_words = prev["word_count"]
                    sim = self._cosine(msg_emb, np.array(prev["embedding"]))

                    # Tuned: similarity > 0.6 (was 0.7) and significant compression
                    # Trigger when current msg is short but similar to a longer message
                    if sim > 0.6 and msg_words < 25 and prev_words > msg_words * 1.5:
                        anomalies.append(Anomaly(
                            type="CROSS_LLM_SHORTHAND",
                            severity="high",
                            llm_id=f"{sender_llm}→{recv_llm}",
                            agent_id=f"{sender}→{receiver}",
                            details={
                                "similarity": round(sim, 3),
                                "current_words": msg_words,
                                "previous_words": prev_words
                            },
                            timestamp=time.time()
                        ))
                        break  # One detection per LLM pair is enough
        return anomalies

    def _fingerprint_mismatch(self, msg: Dict, llm_id: str) -> Optional[Anomaly]:
        """Detect when message length significantly deviates from LLM's typical output."""
        pattern = self.llm_patterns.get(llm_id)
        if not pattern:
            return None

        expected = pattern["avg_words"]
        actual = msg["word_count"]
        deviation = abs(actual - expected)

        # Dynamic threshold: 50% of expected or minimum 20 words deviation
        threshold = max(expected * 0.5, 20)

        if deviation > threshold:
            return Anomaly(
                type="LLM_FINGERPRINT_MISMATCH",
                severity="medium" if deviation < threshold * 2 else "high",
                llm_id=llm_id,
                agent_id=msg["sender"],
                details={
                    "expected": expected,
                    "actual": actual,
                    "deviation": round(deviation, 1),
                    "threshold": round(threshold, 1)
                },
                timestamp=time.time()
            )
        return None

    def _cross_llm_jargon(self, msg: Dict, history: Dict) -> Optional[Anomaly]:
        """
        Detect undefined acronyms/jargon that appear suddenly in conversation.

        Uses the adaptive dictionary system:
        - Known terms (seed + learned) are ignored
        - Unknown terms are tracked as candidates
        - Candidates seen frequently get auto-promoted to learned
        """
        acronyms = re.findall(r'\b[A-Z]{2,}\b', msg["text"])

        # Use adaptive dictionary: filter out known terms (seed + learned)
        unknown = [a for a in acronyms if not self._is_known_term(a) and len(a) >= 2]

        # Track each unknown term as a candidate for future learning
        promoted_terms = []
        for term in unknown:
            if self._track_candidate(term):
                promoted_terms.append(term)

        # Log any promotions for debugging
        if promoted_terms:
            logger.debug(f"Terms auto-promoted to learned: {promoted_terms}")

        # Check if any of these unknown acronyms appeared in previous messages
        # (if they did, they're being used consistently, not suddenly)
        seen_in_history = False
        for agent_h in history.values():
            for llm_h in agent_h.values():
                for m in llm_h:
                    # Skip current message
                    if m.get("message_id") != msg.get("message_id"):
                        if any(a in m["text"] for a in unknown):
                            seen_in_history = True
                            break
                if seen_in_history:
                    break
            if seen_in_history:
                break

        # Only flag as anomaly if unknown terms appear suddenly (not seen before)
        if unknown and not seen_in_history:
            return Anomaly(
                type="CROSS_LLM_JARGON",
                severity="high",
                llm_id=msg["llm_id"],
                agent_id=msg["sender"],
                details={
                    "new_terms": unknown[:5],
                    "candidate_count": len(self.jargon_dict["candidate"]),
                    "learned_count": len(self.jargon_dict["learned"])
                },
                timestamp=time.time()
            )
        return None

    def _detect_hedging_llm(self, text: str) -> Optional[Dict]:
        if not LLM_AVAILABLE:
            return None
        messages = [
            {"role": "system", "content": "You are an expert at detecting hedging/low confidence in AI responses."},
            {"role": "user", "content": f'''Analyze this response for confidence.

Response: "{text}"

Output ONLY valid JSON:
{{
  "confidence": "High" | "Medium" | "Low",
  "hedge_words": ["word1", "word2"] or [],
  "explanation": "brief reason"
}}'''}
        ]
        response = ollama_chat(messages, temperature=0.1)
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"raw_response": response}
        return None

    def _confirm_shorthand_llm(self, prev_text: str, curr_text: str) -> Optional[Dict]:
        if not LLM_AVAILABLE:
            return None
        messages = [
            {"role": "system", "content": "Determine if the current message is shorthand/abbreviated compared to the previous."},
            {"role": "user", "content": f'''Previous message: {prev_text}

Current message: {curr_text}

Output ONLY valid JSON:
{{
  "is_shorthand": true | false,
  "explanation": "brief reason",
  "expanded": "full expanded version if shorthand, else null"
}}'''}
        ]
        response = ollama_chat(messages, temperature=0.2)
        if response:
            try:
                data = json.loads(response)
                return data if data.get("is_shorthand") else None
            except json.JSONDecodeError:
                pass
        return None