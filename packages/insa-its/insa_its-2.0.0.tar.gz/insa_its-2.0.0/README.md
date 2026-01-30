# InsAIts - Making Multi-Agent AI Trustworthy

**Monitor what your AI agents are saying to each other.**

[![PyPI version](https://badge.fury.io/py/insa-its.svg)](https://pypi.org/project/insa-its/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## The Problem

When AI agents communicate with each other, strange things happen:
- **Shorthand emergence** - "Verify customer identity" becomes "Run CVP"
- **Context loss** - Agents suddenly switch topics mid-conversation
- **Jargon creation** - Made-up acronyms that mean nothing to humans
- **Hallucination chains** - One agent's error propagates through the system
- **Anchor drift** - Responses diverge from the user's original question

**In AI-to-human communication, we notice. In AI-to-AI? It's invisible.**

---

## The Solution

InsAIts is a lightweight Python SDK that monitors AI-to-AI communication in real-time.

```python
from insa_its import insAItsMonitor

monitor = insAItsMonitor()

# V2: Set anchor for context-aware detection
monitor.set_anchor("What is quantum computing?")

# Monitor any AI-to-AI message
result = monitor.send_message(
    text=agent_response,
    sender_id="OrderBot",
    receiver_id="InventoryBot",
    llm_id="gpt-4"
)

if result["anomalies"]:
    # V2: Trace the root cause
    for anomaly in result["anomalies"]:
        trace = monitor.trace_root(anomaly)
        print(trace["summary"])
```

**3 lines of code. Full visibility.**

---

## What's New in V2

### Anchor-Aware Detection (Phase 1)
Stop false positives by setting the user's query as an anchor:

```python
# Set user's question as anchor
monitor.set_anchor("Explain quantum computing")

# Responses using "QUBIT", "QPU" won't trigger jargon alerts
# because they're relevant to the query
result = monitor.send_message("Quantum computers use qubits...", "agent1", llm_id="gpt-4o")
```

### Forensic Chain Tracing (Phase 2)
Trace any anomaly back to its root cause:

```python
trace = monitor.trace_root(anomaly)
print(trace["summary"])
# "Jargon 'XYZTERM' first appeared in message from agent_a (gpt-4o)
#  at step 3 of 7. Propagated through 4 subsequent messages."

# ASCII visualization
print(monitor.visualize_chain(anomaly, include_text=True))
```

### Domain Dictionaries (Phase 4)
Load domain-specific terms to reduce false positives:

```python
# Load finance terms (EBITDA, WACC, DCF, etc.)
monitor.load_domain("finance")

# Available domains: finance, healthcare, kubernetes, machine_learning, devops, quantum

# Import/export custom dictionaries
monitor.export_dictionary("my_team_terms.json")
monitor.import_dictionary("shared_terms.json", merge=True)

# Auto-expand unknown terms with LLM
monitor.auto_expand_terms()  # Requires Ollama
```

---

## What It Detects

| Anomaly Type | What It Catches | Severity |
|--------------|-----------------|----------|
| **SHORTHAND_EMERGENCE** | "Process order" -> "PO now" | High |
| **CONTEXT_LOSS** | Marketing meeting -> Recipe discussion | High |
| **CROSS_LLM_JARGON** | Undefined acronyms like "QXRT" | High |
| **ANCHOR_DRIFT** | Response diverges from user's question | High |
| **LLM_FINGERPRINT_MISMATCH** | GPT-4 response that looks like GPT-3.5 | Medium |
| **LOW_CONFIDENCE** | Hedging: "maybe", "I think", "perhaps" | Medium |

---

## Quick Start

### Install

```bash
pip install insa-its
```

For local embeddings (recommended):
```bash
pip install insa-its[full]
```

Or from GitHub:
```bash
pip install git+https://github.com/Nomadu27/InsAIts.git
```

### Use

```python
from insa_its import insAItsMonitor

monitor = insAItsMonitor(session_name="my-agents")

# V2: Set anchor for smarter detection
monitor.set_anchor("Process customer refund request")

# Monitor your agent conversations
result = monitor.send_message(
    text="Process the customer order for SKU-12345",
    sender_id="OrderBot",
    receiver_id="InventoryBot",
    llm_id="gpt-4o-mini"
)

# Check for issues
if result["anomalies"]:
    for anomaly in result["anomalies"]:
        print(f"[{anomaly['severity']}] {anomaly['type']}")
        # V2: Get forensic trace
        trace = monitor.trace_root(anomaly)
        print(f"Root cause: {trace['summary']}")

# Get session health
print(monitor.get_stats())
```

---

## Features

### Real-Time Terminal Dashboard

```python
from insa_its.dashboard import LiveDashboard

dashboard = LiveDashboard(monitor)
dashboard.start()
# Live visualization of all agent communication
```

### LangChain Integration

```python
from insa_its.integrations import LangChainMonitor

monitor = LangChainMonitor()
monitored_chain = monitor.wrap_chain(your_chain, "MyAgent")
```

### CrewAI Integration

```python
from insa_its.integrations import CrewAIMonitor

monitor = CrewAIMonitor()
monitored_crew = monitor.wrap_crew(your_crew)
```

### Decipher Mode

Translate AI-to-AI jargon for human review:

```python
deciphered = monitor.decipher(message)
print(deciphered["expanded_text"])  # Human-readable version
```

Uses local Phi-3 via Ollama - no cloud, no data leaves your machine.

### V2: Domain Dictionaries

```python
# See available domains
print(monitor.get_available_domains())
# ['finance', 'healthcare', 'kubernetes', 'machine_learning', 'devops', 'quantum']

# Load one or more
monitor.load_domain("kubernetes")
monitor.load_domain("devops")

# Terms like K8S, HPA, CI/CD won't trigger false positives
```

### V2: Forensic Chain Visualization

```python
# Get ASCII visualization of anomaly chain
viz = monitor.visualize_chain(anomaly, include_text=True)
print(viz)

# Output:
# ============================================================
# FORENSIC CHAIN TRACE: CROSS_LLM_JARGON
# ============================================================
#
# [Step 1]
#   agent_a -> agent_b (gpt-4o)
#   Words: 15
#   Text: "Let's discuss the implementation..."
#      |
#      v
# [Step 2]
#   agent_b -> agent_a (claude-3.5)
#   Words: 20
#      |
#      v
# [Step 3] >>> ROOT <<< ANOMALY
#   agent_a -> agent_b (gpt-4o)
#   Words: 8
#   Text: "Use XYZPROTO for this..."
#
# ------------------------------------------------------------
# SUMMARY:
# Jargon 'XYZPROTO' first appeared in message from agent_a (gpt-4o)
# at step 3 of 3. Propagated through 0 subsequent messages.
# ============================================================
```

---

## Pricing

### Lifetime Deals - First 100 Users Only!

| Plan | Price | What You Get |
|------|-------|--------------|
| **LIFETIME STARTER** | **EUR99 one-time** | 10K msgs/day forever |
| **LIFETIME PRO** | **EUR299 one-time** | Unlimited forever + priority support |

**Buy Lifetime (Gumroad):**
- [**Lifetime Starter (EUR99)**](https://steddy.gumroad.com/l/InsAItsStarter)
- [**Lifetime Pro (EUR299)**](https://steddy.gumroad.com/l/InsAItsPro100)

**Buy Lifetime (Stripe):**
- [**Lifetime Starter (EUR99)**](https://buy.stripe.com/00w6oH87R77T32A56Eb3q00)
- [**Lifetime Pro (EUR299)**](https://buy.stripe.com/3cI8wPfAjak5bz61Ecb3q04)

---

### Monthly Plans

| Tier | Messages/Day | Price | Best For |
|------|-------------|-------|----------|
| **Free** | 100 | $0 | Testing & evaluation |
| **Starter** | 10,000 | **$49/mo** | Indie devs & small teams |
| **Pro** | Unlimited | **$79/mo** | Production workloads |

**Buy Monthly (Gumroad):**
- [**Monthly Starter ($49/mo)**](https://steddy.gumroad.com/l/InsAItsStarterTier)
- [**Monthly Pro ($79/mo)**](https://steddy.gumroad.com/l/InsAItsProTier)

> **Free tier works without an API key!** Just `pip install insa-its` and start monitoring.

---

## Use Cases

| Industry | Problem Solved |
|----------|----------------|
| **E-Commerce** | Order bots losing context mid-transaction |
| **Customer Service** | Support agents developing incomprehensible shorthand |
| **Finance** | Analysis pipelines hallucinating metrics |
| **Healthcare** | Critical multi-agent systems where errors matter |
| **Research** | Ensuring scientific integrity in AI experiments |

---

## Demo

Try it yourself:

```bash
git clone https://github.com/Nomadu27/InsAIts.git
cd InsAIts
pip install -e .[full] rich

# Run the dashboard demo
python demo_dashboard.py

# Run marketing team simulation
python demo_marketing_team.py
```

---

## Architecture

```
Your Multi-Agent System              InsAIts V2
         |                              |
         |-- user query --------------> |-- set_anchor() [NEW]
         |                              |
         |-- message -----------------> |
         |                              |-- Anchor similarity check [NEW]
         |                              |-- Semantic embedding (local)
         |                              |-- Pattern analysis
         |                              |-- Anomaly detection
         |                              |
         |<-- anomalies, health --------|
         |                              |
         |-- trace_root() ------------> |-- Forensic chain [NEW]
         |<-- summary, visualization ---|
```

**Privacy First:**
- Local embeddings (nothing leaves your machine)
- No raw messages stored in cloud
- API keys hashed before storage
- GDPR-ready

---

## Documentation

| Resource | Link |
|----------|------|
| Installation Guide | [installation_guide.md](installation_guide.md) |
| API Reference | [insaitsapi-production.up.railway.app/docs](https://insaitsapi-production.up.railway.app/docs) |
| Privacy Policy | [PRIVACY_POLICY.md](PRIVACY_POLICY.md) |
| Terms of Service | [TERMS_OF_SERVICE.md](TERMS_OF_SERVICE.md) |

---

## Support

- **Email:** info@yuyai.pro
- **GitHub Issues:** [Report a bug](https://github.com/Nomadu27/InsAIts/issues)
- **API Status:** [insaitsapi-production.up.railway.app](https://insaitsapi-production.up.railway.app)

---

## License

**Proprietary Software** - All rights reserved.

Free tier available for evaluation. Commercial use requires a paid license.
See [LICENSE](LICENSE) for details.

---

<p align="center">
<strong>InsAIts V2 - Making AI Collaboration Trustworthy</strong><br>
<em>Now with Anchor-Aware Detection, Forensic Chain Tracing, and Domain Dictionaries.</em>
</p>
