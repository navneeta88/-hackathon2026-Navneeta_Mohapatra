"""
audit.py — Audit logger for the ShopWave Support Agent.
Logs every tool call, reasoning step, and final outcome per ticket.
"""

import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ToolCallLog:
    tool_name: str
    inputs: dict
    output: Any
    success: bool
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class TicketAudit:
    ticket_id: str
    subject: str
    customer_email: str
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    completed_at: str | None = None
    tool_calls: list[ToolCallLog] = field(default_factory=list)
    reasoning_steps: list[str] = field(default_factory=list)
    final_action: str | None = None      # "refund_issued" | "reply_sent" | "escalated" | "error"
    outcome_summary: str | None = None
    error: str | None = None

    def log_tool_call(self, tool_name: str, inputs: dict, output: Any,
                      success: bool, error: str | None = None):
        self.tool_calls.append(ToolCallLog(
            tool_name=tool_name,
            inputs=inputs,
            output=output,
            success=success,
            error=error,
        ))

    def log_reasoning(self, step: str):
        self.reasoning_steps.append(step)

    def complete(self, action: str, summary: str):
        self.final_action = action
        self.outcome_summary = summary
        self.completed_at = datetime.utcnow().isoformat() + "Z"

    def fail(self, error: str):
        self.error = error
        self.final_action = "error"
        self.completed_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        d = asdict(self)
        return d


class AuditLogger:
    def __init__(self):
        self.records: dict[str, TicketAudit] = {}

    def start(self, ticket_id: str, subject: str, email: str) -> TicketAudit:
        audit = TicketAudit(ticket_id=ticket_id, subject=subject, customer_email=email)
        self.records[ticket_id] = audit
        return audit

    def get(self, ticket_id: str) -> TicketAudit | None:
        return self.records.get(ticket_id)

    def summary(self) -> dict:
        total = len(self.records)
        actions = {}
        for r in self.records.values():
            a = r.final_action or "unknown"
            actions[a] = actions.get(a, 0) + 1
        return {"total_tickets": total, "outcomes": actions}

    def print_report(self):
        print("\n" + "═" * 60)
        print("  SHOPWAVE AGENT — AUDIT REPORT")
        print("═" * 60)
        for ticket_id, rec in self.records.items():
            status_icon = {
                "refund_issued": "✅",
                "reply_sent": "💬",
                "escalated": "🔼",
                "error": "❌",
            }.get(rec.final_action, "❓")
            print(f"\n{status_icon}  {ticket_id} | {rec.subject[:50]}")
            print(f"   Action : {rec.final_action}")
            print(f"   Tools  : {[t.tool_name for t in rec.tool_calls]}")
            print(f"   Summary: {rec.outcome_summary or rec.error or '—'}")
        print("\n" + "─" * 60)
        s = self.summary()
        print(f"  Total: {s['total_tickets']}  |  Outcomes: {s['outcomes']}")
        print("═" * 60 + "\n")

    def save_json(self, path: str = "audit_log.json"):
        with open(path, "w") as f:
            json.dump(
                {tid: rec.to_dict() for tid, rec in self.records.items()},
                f, indent=2, default=str
            )
        print(f"Audit log saved to {path}")
