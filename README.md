# ShopWave Autonomous Support Agent
### Agentic AI Hackathon 2026 Submission

An autonomous customer support agent that resolves ShopWave support tickets using Claude's native tool use, concurrent processing, and full audit logging.

---

## 🚀 Live Demo
👉 https://myovzdy2qenmhwvsnpeomt.streamlit.app/

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Anthropic API key
export ANTHROPIC_API_KEY=your_key_here

# 3. Run the agent
python main.py                     # all 20 tickets
python main.py --limit 3           # first 3 tickets (quick test)
python main.py --ticket TKT-001    # single ticket
```

---

## Project Structure

```
shopwave_agent/
├── main.py          # Entry point & CLI
├── agent.py         # Agentic loop + concurrent orchestrator
├── tools.py         # Mock tool implementations + Claude tool definitions
├── audit.py         # Audit logger
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
Ticket → Claude (reason) → tool_use → execute tool → result → Claude (reason) → ...
                                                                      └── send_reply / escalate
```

### Concurrency
All tickets are processed simultaneously using `asyncio.gather()` — not sequentially.

### Tool Chain (minimum 3 per ticket)
1. `get_customer` — identify customer + tier
2. `get_order` — order status, return deadline
3. `get_product` — warranty, category
4. `check_refund_eligibility` — gated before any refund
5. `issue_refund` — irreversible, always guarded
6. `send_reply` — customer-facing message
7. `escalate` — structured human handoff
8. `search_knowledge_base` — policy lookup

### Error Handling
- Each tool retries up to 2 times on failure (with backoff)
- `check_refund_eligibility` has a 20% simulated timeout rate
- If a tool keeps failing, the agent escalates with the failure context

### Audit Trail
Every ticket produces a full log of tool calls, reasoning steps, and the final outcome, saved to `audit_log.json`.

---

## Hackathon Requirements Checklist

| Requirement | Implementation |
|---|---|
| ≥3 tool calls per chain | Enforced by system prompt + loop |
| Concurrent processing | `asyncio.gather()` over all tickets |
| Graceful tool failure | Retry + escalate fallback |
| Explainable decisions | Full audit log per ticket |
| Escalation with context | `escalate()` with summary + priority |
