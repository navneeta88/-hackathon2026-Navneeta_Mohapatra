# Failure Modes & Handling — ShopWave Autonomous Support Agent

This document describes at least 3 known failure scenarios, how the system detects them, and how it recovers.

---

## Failure Mode 1: Tool Timeout / API Error

**Scenario:**
`check_refund_eligibility` randomly times out (20% failure rate simulated in `tools.py`). This is a hard requirement of the hackathon — at least one tool must fail.

**How it happens:**
```python
if random.random() < FAILURE_RATE:
    raise TimeoutError(f"check_refund_eligibility timed out for {order_id}")
```

**How the agent handles it:**
- The `_execute_tool()` function wraps every tool call in try/except
- On failure, it retries up to 2 times with exponential backoff (0.3s, 0.6s)
- If all retries fail, it returns a structured error dict: `{"error": "Tool failed after 3 attempts: ..."}`
- The LLM receives this error as a tool result and decides to escalate rather than crash
- Audit log records the failure with `success: False` and the error message

**Result:** Agent escalates gracefully with a note that eligibility could not be verified. No crash.

---

## Failure Mode 2: LLM Generates Malformed Tool Call Arguments

**Scenario:**
The LLM generates tool call arguments containing apostrophes or special characters (e.g. `"don't"`, `"I've"`) which break the JSON serialization in Groq's function calling format.

**Error observed:**
```
Failed to call a function. tool_use_failed:
<function=send_reply={"message":"I've checked..."}>
```

**How the agent handles it:**
- `json.loads()` is wrapped in try/except in the tool execution loop
- If argument parsing fails, `tool_input` defaults to `{}` and the error is logged
- System prompt explicitly instructs the model to avoid contractions and special characters in tool arguments
- Audit log captures the malformed call for debugging

**Result:** Agent continues the loop rather than crashing; bad tool call is logged and skipped.

---

## Failure Mode 3: Return Window Expired — Conflicting Customer Expectation

**Scenario:**
Customer requests a refund but their return window has expired. The `check_refund_eligibility` tool returns `eligible: False` with `expired: True`. However, the customer may be VIP tier with special leniency privileges.

**How it happens:**
```json
{
  "eligible": false,
  "reason": "Return window expired on 2024-03-15.",
  "expired": true
}
```

**How the agent handles it:**
- Agent checks customer tier via `get_customer` first (always step 1)
- If tier is `vip` or `premium`, agent searches knowledge base for leniency policy
- Knowledge base returns: *"Premium: Agents may use judgment for borderline cases. VIP: Management pre-approvals may be on file."*
- Agent escalates with full context rather than blindly declining
- Escalation summary includes tier, expiry date, and recommended resolution

**Result:** VIP/Premium customers are never flatly declined — escalated for human judgment with full context.

---

## Failure Mode 4: Refund Amount Exceeds $200 Threshold

**Scenario:**
Refund is technically eligible but the amount exceeds $200, which requires supervisor approval per policy.

**How the agent handles it:**
- After `check_refund_eligibility` returns eligible + amount
- Agent checks if `amount > 200`
- If yes, skips `issue_refund` and calls `escalate` with priority `high`
- Escalation summary includes amount, customer tier, and order details

**Result:** High-value refunds never auto-processed — always routed to human with full context.

---

## Failure Mode 5: Rate Limit Exhaustion (Infrastructure Failure)

**Scenario:**
Free-tier API rate limits (tokens per minute or per day) are exhausted mid-run, especially when processing all 20 tickets.

**How the agent handles it:**
- Each ticket is processed sequentially with a 15-second gap (`asyncio.sleep(15)`)
- If a 429 rate limit error is caught, it is logged in the audit trail with the full error message
- The agent does not crash — remaining tickets continue to be attempted
- Audit log clearly marks affected tickets as `error` with the rate limit reason

**Result:** Partial runs are fully auditable. The system is transparent about what failed and why.
