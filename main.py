"""
main.py — Entry point for the ShopWave Autonomous Support Agent
Usage:
    python main.py                   # process all 20 tickets
    python main.py --limit 3         # process first N tickets (good for testing)
    python main.py --ticket TKT-001  # process a single ticket
"""

import asyncio
import json
import argparse
from pathlib import Path
from agent import run_agent

DATA_DIR = Path(__file__).parent / "data"


def load_tickets(limit: int | None = None, ticket_id: str | None = None) -> list[dict]:
    tickets = json.loads((DATA_DIR / "tickets.json").read_text())
    if ticket_id:
        tickets = [t for t in tickets if t["ticket_id"] == ticket_id]
    if limit:
        tickets = tickets[:limit]
    return tickets


async def main():
    parser = argparse.ArgumentParser(description="ShopWave Autonomous Support Agent")
    parser.add_argument("--limit", type=int, default=None, help="Process only N tickets")
    parser.add_argument("--ticket", type=str, default=None, help="Process a single ticket ID")
    parser.add_argument("--save-audit", type=str, default="audit_log.json",
                        help="Path to save the audit log JSON")
    args = parser.parse_args()

    tickets = load_tickets(limit=args.limit, ticket_id=args.ticket)
    if not tickets:
        print("No tickets found matching your criteria.")
        return

    audit_logger = await run_agent(tickets)
    audit_logger.print_report()
    audit_logger.save_json(args.save_audit)


if __name__ == "__main__":
    asyncio.run(main())
