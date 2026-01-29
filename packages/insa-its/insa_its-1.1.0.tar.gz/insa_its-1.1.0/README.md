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

**In AI-to-human communication, we notice. In AI-to-AI? It's invisible.**

---

## The Solution

InsAIts is a lightweight Python SDK that monitors AI-to-AI communication in real-time.

```python
from insa_its import insAItsMonitor

monitor = insAItsMonitor()

# Monitor any AI-to-AI message
result = monitor.send_message(
    text=agent_response,
    sender_id="OrderBot",
    receiver_id="InventoryBot",
    llm_id="gpt-4"
)

if result["anomalies"]:
    print("Warning:", result["anomalies"])
```

**3 lines of code. Full visibility.**

---

## What It Detects

| Anomaly Type | What It Catches | Severity |
|--------------|-----------------|----------|
| **SHORTHAND_EMERGENCE** | "Process order" -> "PO now" | High |
| **CONTEXT_LOSS** | Marketing meeting -> Recipe discussion | High |
| **CROSS_LLM_JARGON** | Undefined acronyms like "QXRT" | High |
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

---

## Pricing

### Limited Launch Offer - First 100 Users Only!

| Plan | Price | What You Get |
|------|-------|--------------|
| **LIFETIME STARTER** | **€99 one-time** | 10K msgs/day forever |
| **LIFETIME PRO** | **$299 one-time** | Unlimited forever + priority support |

[**Get Lifetime Starter (€99)**](https://buy.stripe.com/00w6oH87R77T32A56Eb3q00) | [**Get Lifetime Pro ($299)**](https://buy.stripe.com/3cI8wPfAjak5bz61Ecb3q04)

### Monthly Plans

| Tier | Messages/Day | Price | Best For |
|------|-------------|-------|----------|
| **Free** | 100 | $0 | Testing & evaluation |
| **Starter** | 10,000 | **$29/mo** | Indie devs & small teams |
| **Pro** | Unlimited | **$79/mo** | Production workloads |

[**Get Starter ($29/mo)**](https://buy.stripe.com/4gM14ngEn8bX9qYfv2b3q05) | [**Get Pro ($79/mo)**](https://buy.stripe.com/bJebJ1afZak5gTqgz6b3q06)

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
Your Multi-Agent System              InsAIts
         |                              |
         |-- message -----------------> |
         |                              |-- Semantic embedding (local)
         |                              |-- Pattern analysis
         |                              |-- Anomaly detection
         |                              |
         |<-- anomalies, health --------|
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
<strong>InsAIts - Making AI Collaboration Trustworthy</strong><br>
<em>Built by developers who believe multi-agent AI should be transparent.</em>
</p>
