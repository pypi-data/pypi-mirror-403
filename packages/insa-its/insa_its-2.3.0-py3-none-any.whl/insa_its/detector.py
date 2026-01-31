import numpy as np
import re
import json
import os
import logging
from pathlib import Path
from typing import Any, List, Dict, Optional, Set
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

# V2: Domain-specific dictionaries for reducing false positives
DOMAIN_DICTIONARIES: Dict[str, Dict[str, Any]] = {
    "finance": {
        "known": {
            "EBITDA", "P&L", "ROI", "CAGR", "AUM", "NAV", "YTD", "QTD", "MTD",
            "WACC", "DCF", "NPV", "IRR", "EPS", "PE", "PB", "ROIC", "ROCE",
            "CAPEX", "OPEX", "FCF", "LBO", "M&A", "IPO", "SPV", "ABS", "MBS",
            "CDO", "CDS", "OTC", "FX", "FRA", "IRS", "LIBOR", "SOFR", "EURIBOR"
        },
        "expansions": {
            "EBITDA": "Earnings Before Interest, Taxes, Depreciation, and Amortization",
            "WACC": "Weighted Average Cost of Capital",
            "DCF": "Discounted Cash Flow",
            "NPV": "Net Present Value",
            "IRR": "Internal Rate of Return",
            "EPS": "Earnings Per Share",
            "CAPEX": "Capital Expenditure",
            "OPEX": "Operating Expenditure",
            "FCF": "Free Cash Flow",
            "LBO": "Leveraged Buyout",
            "ABS": "Asset-Backed Securities",
            "MBS": "Mortgage-Backed Securities",
            "CDO": "Collateralized Debt Obligation",
            "CDS": "Credit Default Swap"
        }
    },
    "healthcare": {
        "known": {
            "HIPAA", "PHI", "EHR", "EMR", "ICD", "CPT", "DRG", "HMO", "PPO",
            "PCP", "RN", "MD", "DO", "NP", "PA", "ICU", "ER", "OR", "NICU",
            "FDA", "CDC", "WHO", "NIH", "CMS", "HRSA", "ONC", "AHRQ",
            "SNOMED", "LOINC", "HL7", "FHIR", "ADT", "CCR", "CCD", "CCDA"
        },
        "expansions": {
            "HIPAA": "Health Insurance Portability and Accountability Act",
            "PHI": "Protected Health Information",
            "EHR": "Electronic Health Record",
            "EMR": "Electronic Medical Record",
            "ICD": "International Classification of Diseases",
            "CPT": "Current Procedural Terminology",
            "DRG": "Diagnosis-Related Group",
            "FHIR": "Fast Healthcare Interoperability Resources",
            "HL7": "Health Level Seven International",
            "SNOMED": "Systematized Nomenclature of Medicine"
        }
    },
    "kubernetes": {
        "known": {
            "K8S", "POD", "HELM", "KUBECTL", "CRD", "HPA", "VPA", "PVC", "PV",
            "RBAC", "CNI", "CSI", "CRI", "ETCD", "ISTIO", "ENVOY", "NGINX",
            "DAEMONSET", "STATEFULSET", "REPLICASET", "CONFIGMAP", "SECRET",
            "INGRESS", "EGRESS", "SVC", "NS", "SA", "CM", "NODEPORT", "LB"
        },
        "expansions": {
            "K8S": "Kubernetes",
            "HPA": "Horizontal Pod Autoscaler",
            "VPA": "Vertical Pod Autoscaler",
            "PVC": "Persistent Volume Claim",
            "PV": "Persistent Volume",
            "RBAC": "Role-Based Access Control",
            "CNI": "Container Network Interface",
            "CSI": "Container Storage Interface",
            "CRI": "Container Runtime Interface",
            "CRD": "Custom Resource Definition"
        }
    },
    "machine_learning": {
        "known": {
            "BERT", "GPT", "LSTM", "RNN", "CNN", "GAN", "VAE", "AE", "MLP",
            "SOTA", "FLOPS", "TPU", "CUDA", "ONNX", "RLHF", "DPO", "PPO",
            "ADAM", "SGD", "MSE", "MAE", "BCE", "NLL", "KL", "BLEU", "ROUGE",
            "F1", "AUC", "ROC", "PR", "AP", "MAP", "IOU", "YOLO", "RCNN"
        },
        "expansions": {
            "BERT": "Bidirectional Encoder Representations from Transformers",
            "GPT": "Generative Pre-trained Transformer",
            "LSTM": "Long Short-Term Memory",
            "RLHF": "Reinforcement Learning from Human Feedback",
            "DPO": "Direct Preference Optimization",
            "SOTA": "State of the Art",
            "ONNX": "Open Neural Network Exchange",
            "BLEU": "Bilingual Evaluation Understudy",
            "ROUGE": "Recall-Oriented Understudy for Gisting Evaluation"
        }
    },
    "devops": {
        "known": {
            "CI", "CD", "CICD", "IaC", "SRE", "SLO", "SLI", "SLA", "MTTR",
            "MTTF", "MTBF", "RTO", "RPO", "DR", "HA", "FT", "LB", "CDN",
            "APM", "ELK", "SIEM", "WAF", "DDoS", "TLS", "mTLS", "PKI",
            "OIDC", "SAML", "OAuth", "JWT", "JWK", "JWKS"
        },
        "expansions": {
            "CI": "Continuous Integration",
            "CD": "Continuous Deployment/Delivery",
            "IaC": "Infrastructure as Code",
            "SRE": "Site Reliability Engineering",
            "SLO": "Service Level Objective",
            "SLI": "Service Level Indicator",
            "MTTR": "Mean Time To Recovery",
            "MTTF": "Mean Time To Failure",
            "RTO": "Recovery Time Objective",
            "RPO": "Recovery Point Objective"
        }
    },
    "quantum": {
        "known": {
            "QUBIT", "QPU", "QC", "QML", "NISQ", "VQE", "QAOA", "QFT", "QPE",
            "CNOT", "SWAP", "TOFFOLI", "HADAMARD", "PAULI", "BLOCH",
            "IBM", "IBMQ", "CIRQ", "QISKIT", "PENNYLANE", "BRAKET"
        },
        "expansions": {
            "QUBIT": "Quantum Bit",
            "QPU": "Quantum Processing Unit",
            "QML": "Quantum Machine Learning",
            "NISQ": "Noisy Intermediate-Scale Quantum",
            "VQE": "Variational Quantum Eigensolver",
            "QAOA": "Quantum Approximate Optimization Algorithm",
            "QFT": "Quantum Fourier Transform",
            "QPE": "Quantum Phase Estimation"
        }
    }
}

@dataclass
class Anomaly:
    type: str
    severity: str
    llm_id: str
    agent_id: str
    details: Dict
    timestamp: float
    # V2 fields for forensic tracing and anchor-aware detection
    message_id: str = ""
    root_message_id: Optional[str] = None
    drift_chain: List[str] = field(default_factory=list)
    anchor_similarity: Optional[float] = None

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
        self.jargon_dict: Dict[str, Any] = {
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

    # ============================================
    # V2: DOMAIN DICTIONARY MANAGEMENT (Phase 4)
    # ============================================

    def load_domain(self, domain: str) -> Dict:
        """
        Load a domain-specific dictionary to reduce false positives.

        Args:
            domain: Domain name (finance, healthcare, kubernetes, machine_learning, devops, quantum)

        Returns:
            Dict with loaded domain info and terms added
        """
        if domain not in DOMAIN_DICTIONARIES:
            available = list(DOMAIN_DICTIONARIES.keys())
            return {"error": f"Unknown domain: {domain}", "available_domains": available}

        domain_data = DOMAIN_DICTIONARIES[domain]

        # Merge with existing known terms
        terms_before = len(self.jargon_dict["known"])
        self.jargon_dict["known"].update(domain_data["known"])
        terms_added = len(self.jargon_dict["known"]) - terms_before

        # Merge expansions
        expansions_before = len(self.jargon_dict["expanded"])
        self.jargon_dict["expanded"].update(domain_data.get("expansions", {}))
        expansions_added = len(self.jargon_dict["expanded"]) - expansions_before

        self._save_dict()

        logger.info(f"Loaded domain '{domain}': {terms_added} terms, {expansions_added} expansions")

        return {
            "loaded": domain,
            "terms_added": terms_added,
            "expansions_added": expansions_added,
            "total_known": len(self.jargon_dict["known"]),
            "total_expanded": len(self.jargon_dict["expanded"])
        }

    def get_available_domains(self) -> List[str]:
        """Return list of available domain dictionaries."""
        return list(DOMAIN_DICTIONARIES.keys())

    def export_dictionary(self, filepath: str) -> Dict:
        """
        Export the current dictionary to a JSON file.

        Args:
            filepath: Path to save the dictionary JSON file

        Returns:
            Dict with export status and statistics
        """
        data = {
            "known": list(self.jargon_dict["known"]),
            "learned": list(self.jargon_dict["learned"]),
            "expanded": self.jargon_dict["expanded"],
            "metadata": {
                "exported_at": time.time(),
                "version": "2.0",
                "known_count": len(self.jargon_dict["known"]),
                "learned_count": len(self.jargon_dict["learned"]),
                "expanded_count": len(self.jargon_dict["expanded"])
            }
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Exported dictionary to {filepath}")

            return {
                "exported": filepath,
                "total_terms": len(data["known"]) + len(data["learned"]),
                "known_terms": len(data["known"]),
                "learned_terms": len(data["learned"]),
                "expanded_terms": len(data["expanded"])
            }
        except Exception as e:
            logger.error(f"Failed to export dictionary: {e}", exc_info=True)
            return {"error": str(e)}

    def import_dictionary(self, filepath: str, merge: bool = True) -> Dict:
        """
        Import a dictionary from a JSON file.

        Args:
            filepath: Path to the dictionary JSON file
            merge: If True, merge with existing. If False, replace.

        Returns:
            Dict with import status and statistics
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            known_before = len(self.jargon_dict["known"])
            learned_before = len(self.jargon_dict["learned"])
            expanded_before = len(self.jargon_dict["expanded"])

            if merge:
                self.jargon_dict["known"].update(set(data.get("known", [])))
                self.jargon_dict["learned"].update(set(data.get("learned", [])))
                self.jargon_dict["expanded"].update(data.get("expanded", {}))
            else:
                # Keep seed terms, replace learned/expanded
                imported_known = set(data.get("known", []))
                self.jargon_dict["known"] = self._get_seed_terms().union(imported_known)
                self.jargon_dict["learned"] = set(data.get("learned", []))
                self.jargon_dict["expanded"] = data.get("expanded", {})

            self._save_dict()

            known_added = len(self.jargon_dict["known"]) - known_before
            learned_added = len(self.jargon_dict["learned"]) - learned_before
            expanded_added = len(self.jargon_dict["expanded"]) - expanded_before

            logger.info(f"Imported dictionary from {filepath} (merge={merge})")

            return {
                "imported": filepath,
                "mode": "merge" if merge else "replace",
                "known_added": known_added,
                "learned_added": learned_added,
                "expanded_added": expanded_added,
                "total_known": len(self.jargon_dict["known"]),
                "total_learned": len(self.jargon_dict["learned"]),
                "total_expanded": len(self.jargon_dict["expanded"])
            }
        except FileNotFoundError:
            return {"error": f"File not found: {filepath}"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {e}"}
        except Exception as e:
            logger.error(f"Failed to import dictionary: {e}", exc_info=True)
            return {"error": str(e)}

    def auto_expand_terms(
        self,
        terms: Optional[List[str]] = None,
        model: str = "phi3"
    ) -> Dict:
        """
        Use LLM to automatically expand undefined terms.

        Args:
            terms: List of terms to expand. If None, expands all learned terms without expansions.
            model: Ollama model to use for expansion

        Returns:
            Dict with expanded terms and statistics
        """
        if not LLM_AVAILABLE:
            return {"error": "LLM not available (Ollama required)"}

        if terms is None:
            # Find learned terms without expansions
            terms = [
                t for t in self.jargon_dict["learned"]
                if t not in self.jargon_dict["expanded"]
            ]

        if not terms:
            return {"status": "all_terms_expanded", "expanded": {}}

        expansions = {}
        errors = []

        # Limit to 20 at a time to avoid overwhelming the LLM
        for term in terms[:20]:
            messages = [{
                "role": "user",
                "content": f"What does the acronym '{term}' stand for? Reply with ONLY the expansion, nothing else. If unknown, reply 'UNKNOWN'."
            }]

            try:
                response = ollama_chat(messages, model=model, temperature=0.1)
                if response and len(response) < 200 and "UNKNOWN" not in response.upper():
                    expansion = response.strip()
                    expansions[term] = expansion
                    self.jargon_dict["expanded"][term] = expansion
            except Exception as e:
                errors.append({"term": term, "error": str(e)})

        if expansions:
            self._save_dict()

        logger.info(f"Auto-expanded {len(expansions)} terms")

        return {
            "expanded": expansions,
            "count": len(expansions),
            "remaining": len(terms) - len(expansions) - len(errors),
            "errors": errors if errors else None
        }

    # ============================================
    # V2: ANCHOR-AWARE DETECTION HELPERS (Phase 1)
    # ============================================

    def _terms_relevant_to_anchor(
        self,
        terms: List[str],
        anchor_text: str
    ) -> bool:
        """
        Check if the new terms are likely relevant to the user's query.

        Example:
        - Query: "Explain quantum computing"
        - Terms: ["QUBITS", "QPU"]
        - Returns: True (these are relevant to quantum computing)
        """
        if not terms:
            return False

        anchor_lower = anchor_text.lower()

        # Domain keywords that indicate technical queries
        domain_indicators = {
            "quantum": ["qubit", "qpu", "superposition", "entangle", "nisq", "qml"],
            "machine learning": ["ml", "nn", "cnn", "rnn", "llm", "gpu", "bert", "gpt", "lstm"],
            "kubernetes": ["k8s", "pod", "helm", "kubectl", "container", "docker"],
            "finance": ["ebitda", "roi", "wacc", "dcf", "npv", "irr", "capex"],
            "healthcare": ["hipaa", "phi", "ehr", "emr", "fhir", "hl7"],
            "devops": ["ci", "cd", "sre", "slo", "sli", "mttr", "rto"],
            "api": ["rest", "graphql", "endpoint", "oauth", "jwt", "http"],
            "database": ["sql", "nosql", "orm", "acid", "crud", "index"],
            "cloud": ["aws", "gcp", "azure", "ec2", "s3", "lambda", "serverless"],
        }

        for domain, keywords in domain_indicators.items():
            if domain in anchor_lower:
                for term in terms:
                    if term.lower() in keywords:
                        return True

        # Also check if terms appear directly in the anchor
        for term in terms:
            if term.lower() in anchor_lower:
                return True

        # Fallback: Use LLM to check relevance
        if LLM_AVAILABLE:
            return self._llm_check_relevance(terms, anchor_text)

        return False

    def _llm_check_relevance(
        self,
        terms: List[str],
        anchor_text: str
    ) -> bool:
        """Use LLM to determine if terms are relevant to the anchor query."""
        messages = [{
            "role": "user",
            "content": f'''Are the following terms relevant to this query?

Query: "{anchor_text}"
Terms: {", ".join(terms)}

Reply with ONLY "YES" or "NO".'''
        }]

        try:
            response = ollama_chat(messages, temperature=0.1)
            if response:
                return response.strip().upper() == "YES"
        except Exception:
            pass

        return False

    def detect(
        self,
        current_msg: Dict,
        history: Dict[str, Dict[str, List[Dict]]],
        sender_id: str,
        llm_id: str,
        receiver_id: Optional[str] = None,
        anchor: Optional[Dict] = None  # V2: pass anchor for context-aware detection
    ) -> List[Anomaly]:
        anomalies = []
        agent_hist = history.get(sender_id, {})
        llm_hist = agent_hist.get(llm_id, [])

        # V2: Calculate anchor similarity FIRST (for false positive suppression)
        anchor_similarity = None
        if anchor and anchor.get("embedding") is not None:
            anchor_emb = np.array(anchor["embedding"])
            msg_emb = np.array(current_msg["embedding"])
            anchor_similarity = self._cosine(anchor_emb, msg_emb)

        # Always check jargon detection (doesn't need history)
        jargon = self._cross_llm_jargon(current_msg, history)
        if jargon:
            anomalies.append(jargon)

        # Always check fingerprint mismatch (doesn't need history)
        mismatch = self._fingerprint_mismatch(current_msg, llm_id)
        if mismatch:
            anomalies.append(mismatch)

        # V2: Check for ANCHOR_DRIFT (response drifts from original query)
        if anchor_similarity is not None and anchor_similarity < 0.4:
            anomalies.append(Anomaly(
                type="ANCHOR_DRIFT",
                severity="high",
                llm_id=llm_id,
                agent_id=sender_id,
                details={
                    "anchor_similarity": round(anchor_similarity, 3),
                    "anchor_text_preview": anchor.get("text", "")[:100],
                    "response_preview": current_msg["text"][:100]
                },
                timestamp=time.time(),
                message_id=current_msg.get("message_id", ""),
                anchor_similarity=anchor_similarity
            ))

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
                        timestamp=time.time(),
                        message_id=current_msg.get("message_id", ""),
                        anchor_similarity=anchor_similarity
                    ))
            # V2: Apply anchor-based false positive suppression before returning
            anomalies = self._suppress_anchor_aligned(anomalies, anchor, anchor_similarity)
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
                timestamp=time.time(),
                message_id=current_msg.get("message_id", ""),
                anchor_similarity=anchor_similarity
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
                timestamp=time.time(),
                message_id=current_msg.get("message_id", ""),
                anchor_similarity=anchor_similarity
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
                    timestamp=time.time(),
                    message_id=current_msg.get("message_id", ""),
                    anchor_similarity=anchor_similarity
                ))

        # V2: Apply anchor-based false positive suppression
        anomalies = self._suppress_anchor_aligned(anomalies, anchor, anchor_similarity)

        return anomalies

    def _suppress_anchor_aligned(
        self,
        anomalies: List[Anomaly],
        anchor: Optional[Dict],
        anchor_similarity: Optional[float]
    ) -> List[Anomaly]:
        """
        V2: Suppress false positives when response is aligned with anchor query.

        If anchor_similarity > 0.6, new terms that are relevant to the query
        are downgraded to "info" severity instead of "high".
        """
        if anchor is None or anchor_similarity is None:
            return anomalies

        if anchor_similarity <= 0.6:
            return anomalies

        anchor_text = anchor.get("text", "")
        if not anchor_text:
            return anomalies

        for anomaly in anomalies:
            if anomaly.type == "CROSS_LLM_JARGON":
                new_terms = anomaly.details.get("new_terms", [])
                if new_terms and self._terms_relevant_to_anchor(new_terms, anchor_text):
                    # Downgrade severity - terms are relevant to user's query
                    anomaly.severity = "info"
                    anomaly.details["suppressed"] = True
                    anomaly.details["reason"] = "Terms relevant to user query"

            # Also attach anchor_similarity to all anomalies
            anomaly.anchor_similarity = anchor_similarity

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