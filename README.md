# ShopWave Autonomous Support Agent
### Agentic AI Hackathon 2026 — Navneeta Mohapatra

An autonomous customer support agent that resolves ShopWave support tickets using **Groq + Llama-3.3-70B**, sequential async processing, and full audit logging.

---

## 🚀 Live Demo
👉 https://myovzdy2qenmhwvsnpeomt.streamlit.app/

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Groq API key (free at console.groq.com)
set GROQ_API_KEY=your_key_here        # Windows
export GROQ_API_KEY=your_key_here     # Mac/Linux

# 3. Run the agent
python main.py                     # all 20 tickets
python main.py --limit 3           # first 3 tickets (quick test)
python main.py --ticket TKT-001    # single ticket

# 4. Launch the Streamlit dashboard
python -m streamlit run streamlit_app.py
```

---

## Project Structure

```
shopwave_agent/
├── main.py              # Entry point & CLI
├── agent.py             # Agentic loop + orchestrator
├── tools.py             # 8 mock tool implementations
├── audit.py             # Audit logger
├── streamlit_app.py     # Live dashboard UI
├── architecture.png     # System architecture diagram
├── failure_modes.md     # 5 documented failure scenarios
├── audit_log.json       # Generated output — all 20 tickets
├── requirements.txt
└── data/
    ├── tickets.json
    ├── customers.json
    ├── orders.json
    ├── products.json
    └── knowledge-base.md
```

---

## Architecture

### Agentic Loop (per ticket)
```
Ticket → LLM (reason) → tool_use → execute tool → result → LLM (reason) → ...
                                                                └── send_reply / escalate
```

### Tool Chain (minimum 3 per ticket)
1. `get_customer` — identify customer + tier
2. `get_order` — order status, return deadline
3. `get_product` — warranty, category
4. `check_refund_eligibility` — gated before any refund (20% simulated timeout)
5. `issue_refund` — irreversible, always guarded
6. `send_reply` — customer-facing message
7. `escalate` — structured human handoff with priority
8. `search_knowledge_base` — policy lookup

### Error Handling
- Each tool retries up to 2 times on failure with exponential backoff
- `check_refund_eligibility` has a 20% simulated timeout rate
- If a tool keeps failing, the agent escalates with failure context
- Rate limit errors are logged in audit trail — agent never crashes

### Audit Trail
Every ticket produces a full log of tool calls, reasoning steps, and final outcome saved to `audit_log.json`.

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Llama-3.3-70B via Groq |
| Concurrency | Python asyncio (sequential + 15s gap) |
| Tool Execution | 8 async mock tools backed by JSON |
| Audit Logging | Full JSON trace per ticket |
| Dashboard | Streamlit |

---

## Hackathon Requirements

| Requirement | Implementation |
|---|---|
| ≥3 tool calls per chain | Enforced by system prompt + agentic loop |
| Concurrent processing | asyncio sequential with rate-limit handling |
| Graceful tool failure | Retry x2 + escalate fallback |
| Explainable decisions | Full audit log per ticket |
| Escalation with context | `escalate()` with summary + priority level |
| All 5 deliverables | README, architecture.png, failure_modes.md, audit_log.json, demo |
