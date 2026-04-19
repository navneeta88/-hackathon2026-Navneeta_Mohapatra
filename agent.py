"""
agent.py — ShopWave Autonomous Support Agent
Uses Groq (free tier) with Llama function calling.
"""

import json
import asyncio
import os
from groq import Groq
from audit import AuditLogger, TicketAudit
from tools import TOOL_REGISTRY, GROQ_TOOLS

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL = "llama-3.3-70b-versatile"
MAX_TOOL_RETRIES = 2
MAX_AGENT_ITERATIONS = 10

SYSTEM_PROMPT = """You are an autonomous customer support agent for ShopWave, an e-commerce platform.
Your job is to resolve customer support tickets fully and correctly using the tools available to you.

Your Process (follow this for every ticket):
1. ALWAYS start by calling get_customer to identify the customer and their tier.
2. If an order ID is mentioned, call get_order to get order details.
3. If the product matters, call get_product for warranty/return info.
4. For refund/return requests: call check_refund_eligibility before any refund.
5. If eligible: call issue_refund, then send_reply with a clear resolution message.
6. If not eligible: search_knowledge_base for the relevant policy, then send_reply explaining why.
7. Escalate when: refund > $200, warranty claim, conflicting data, or you are uncertain.

Rules:
- NEVER issue a refund without first checking eligibility.
- ALWAYS address the customer by first name in replies.
- Be empathetic and professional. Explain decisions clearly.
- If a tool fails or times out, retry once. If it fails again, escalate with that context.
- You MUST make at least 3 tool calls per ticket.
- End every ticket with either send_reply OR escalate — never leave it unresolved.

Escalation priorities: urgent=fraud/safety, high=refund>$200/warranty, medium=borderline, low=general
"""


# ── Tool executor ─────────────────────────────────────────────────────────────

async def _execute_tool(tool_name: str, tool_input: dict, audit: TicketAudit) -> str:
    fn = TOOL_REGISTRY.get(tool_name)
    if not fn:
        result = {"error": f"Unknown tool: {tool_name}"}
        audit.log_tool_call(tool_name, tool_input, result, success=False, error="Unknown tool")
        return json.dumps(result)

    last_error = None
    for attempt in range(MAX_TOOL_RETRIES + 1):
        try:
            result = await fn(**tool_input)
            audit.log_tool_call(tool_name, tool_input, result, success=True)
            return json.dumps(result, default=str)
        except Exception as e:
            last_error = str(e)
            if attempt < MAX_TOOL_RETRIES:
                await asyncio.sleep(0.3 * (attempt + 1))
            else:
                error_result = {"error": f"Tool '{tool_name}' failed: {last_error}"}
                audit.log_tool_call(tool_name, tool_input, error_result,
                                    success=False, error=last_error)
                return json.dumps(error_result)


# ── Per-ticket agent ──────────────────────────────────────────────────────────

async def process_ticket(ticket: dict, client: Groq, audit_logger: AuditLogger) -> dict:
    ticket_id = ticket["ticket_id"]
    email = ticket["customer_email"]
    subject = ticket["subject"]
    body = ticket["body"]

    audit = audit_logger.start(ticket_id, subject, email)
    audit.log_reasoning(f"Starting ticket: {subject}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Support ticket received:\n\n"
                f"Ticket ID: {ticket_id}\n"
                f"From: {email}\n"
                f"Subject: {subject}\n\n"
                f"Message:\n{body}\n\n"
                f"Please resolve this ticket fully."
            ),
        },
    ]

    final_action = "unknown"
    outcome_summary = "Agent loop ended without explicit resolution."

    try:
        for iteration in range(MAX_AGENT_ITERATIONS):
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=MODEL,
                messages=messages,
                tools=GROQ_TOOLS,
                tool_choice="auto",
                max_tokens=2048,
            )

            msg = response.choices[0].message
            messages.append(msg)

            # Log any text reasoning
            if msg.content:
                audit.log_reasoning(msg.content[:300])

            # No more tool calls — done
            if not msg.tool_calls:
                outcome_summary = "Agent completed reasoning."
                break

            # Execute all tool calls
            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_input = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_input = {}

                print(f"  [{ticket_id}] → {tool_name}({list(tool_input.keys())})")

                result_str = await _execute_tool(tool_name, tool_input, audit)

                # Track final action
                if tool_name == "issue_refund":
                    final_action = "refund_issued"
                    outcome_summary = f"Refund issued for {tool_input.get('order_id')}."
                elif tool_name == "send_reply" and final_action != "refund_issued":
                    final_action = "reply_sent"
                    outcome_summary = "Reply sent to customer."
                elif tool_name == "escalate":
                    final_action = "escalated"
                    outcome_summary = f"Escalated: {tool_input.get('summary', '')[:120]}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str,
                })

    except Exception as e:
        audit.fail(f"Groq API error: {e}")
        return {"ticket_id": ticket_id, "status": "error", "error": str(e)}

    audit.complete(final_action, outcome_summary)
    return {
        "ticket_id": ticket_id,
        "status": final_action,
        "summary": outcome_summary,
        "tool_calls_made": len(audit.tool_calls),
    }


# ── Orchestrator ──────────────────────────────────────────────────────────────

async def run_agent(tickets: list[dict]) -> AuditLogger:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set.")

    client = Groq(api_key=api_key)
    audit_logger = AuditLogger()

    print(f"\n🚀 ShopWave Agent starting — {len(tickets)} tickets\n")

    # Process sequentially with delay to respect Groq free tier rate limits
    for i, ticket in enumerate(tickets):
        if i > 0:
            print(f"  ⏳ Waiting 15s before next ticket (rate limit)...")
            await asyncio.sleep(15)
        await process_ticket(ticket, client, audit_logger)

    return audit_logger
