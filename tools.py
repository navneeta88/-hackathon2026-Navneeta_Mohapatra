"""
tools.py — Mock tool implementations for ShopWave Support Agent
Backed by local JSON/Markdown data files.
One tool (check_refund_eligibility) has simulated failures for realism.
"""

import json
import random
import asyncio
from pathlib import Path
from datetime import datetime, date

# ── Data loading ──────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"

def _load(filename):
    with open(DATA_DIR / filename) as f:
        return json.load(f)

CUSTOMERS = {c["customer_id"]: c for c in _load("customers.json")}
CUSTOMERS_BY_EMAIL = {c["email"]: c for c in CUSTOMERS.values()}
ORDERS = {o["order_id"]: o for o in _load("orders.json")}
PRODUCTS = {p["product_id"]: p for p in _load("products.json")}
KNOWLEDGE_BASE = (DATA_DIR / "knowledge-base.md").read_text()

FAILURE_RATE = 0.20  # 20% chance check_refund_eligibility times out


# ── Tool implementations ──────────────────────────────────────────────────────

async def get_customer(email: str) -> dict:
    await asyncio.sleep(0.05)
    customer = CUSTOMERS_BY_EMAIL.get(email)
    if not customer:
        return {"error": f"No customer found with email: {email}"}
    return {
        "customer_id": customer["customer_id"],
        "name": customer["name"],
        "email": customer["email"],
        "tier": customer["tier"],
        "member_since": customer["member_since"],
        "total_orders": customer["total_orders"],
        "total_spent": customer["total_spent"],
        "notes": customer.get("notes", ""),
    }


async def get_order(order_id: str) -> dict:
    await asyncio.sleep(0.05)
    order = ORDERS.get(order_id)
    if not order:
        return {"error": f"Order not found: {order_id}"}
    return {
        "order_id": order["order_id"],
        "customer_id": order["customer_id"],
        "product_id": order["product_id"],
        "quantity": order["quantity"],
        "amount": order["amount"],
        "status": order["status"],
        "order_date": order["order_date"],
        "delivery_date": order.get("delivery_date"),
        "return_deadline": order.get("return_deadline"),
        "refund_status": order.get("refund_status"),
        "notes": order.get("notes", ""),
    }


async def get_product(product_id: str) -> dict:
    await asyncio.sleep(0.05)
    product = PRODUCTS.get(product_id)
    if not product:
        return {"error": f"Product not found: {product_id}"}
    return {
        "product_id": product["product_id"],
        "name": product["name"],
        "category": product["category"],
        "price": product["price"],
        "warranty_months": product["warranty_months"],
        "return_window_days": product["return_window_days"],
        "returnable": product["returnable"],
        "notes": product.get("notes", ""),
    }


async def search_knowledge_base(query: str) -> dict:
    await asyncio.sleep(0.05)
    query_lower = query.lower()
    keywords = query_lower.split()
    sections = KNOWLEDGE_BASE.split("\n## ")
    results = []
    for section in sections:
        score = sum(section.lower().count(kw) for kw in keywords)
        if score > 0:
            results.append((score, section[:800]))
    results.sort(reverse=True)
    if not results:
        return {"result": "No relevant policy found for this query."}
    return {"result": "\n\n---\n\n".join(text for _, text in results[:2])}


async def check_refund_eligibility(order_id: str) -> dict:
    if random.random() < FAILURE_RATE:
        raise TimeoutError(f"check_refund_eligibility timed out for {order_id}")
    await asyncio.sleep(0.1)
    order = ORDERS.get(order_id)
    if not order:
        return {"eligible": False, "reason": f"Order {order_id} not found."}
    if order.get("refund_status") == "refunded":
        return {"eligible": False, "reason": "Order has already been refunded."}
    if order["status"] == "cancelled":
        return {"eligible": False, "reason": "Order was cancelled."}
    return_deadline = order.get("return_deadline")
    if return_deadline:
        deadline = date.fromisoformat(return_deadline)
        if date.today() > deadline:
            return {
                "eligible": False,
                "reason": f"Return window expired on {return_deadline}.",
                "expired": True,
                "amount": order["amount"],
            }
    return {
        "eligible": True,
        "reason": "Order is within return window and eligible for refund.",
        "amount": order["amount"],
    }


async def issue_refund(order_id: str, amount: float) -> dict:
    await asyncio.sleep(0.1)
    order = ORDERS.get(order_id)
    if not order:
        return {"success": False, "error": f"Order {order_id} not found."}
    if order.get("refund_status") == "refunded":
        return {"success": False, "error": "Order already refunded."}
    order["refund_status"] = "refunded"
    return {
        "success": True,
        "order_id": order_id,
        "amount_refunded": amount,
        "message": f"Refund of ${amount:.2f} issued. Will appear in 5–7 business days.",
    }


async def send_reply(ticket_id: str, message: str) -> dict:
    await asyncio.sleep(0.05)
    return {
        "success": True,
        "ticket_id": ticket_id,
        "message_sent": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


async def escalate(ticket_id: str, summary: str, priority: str) -> dict:
    await asyncio.sleep(0.05)
    valid_priorities = {"low", "medium", "high", "urgent"}
    if priority not in valid_priorities:
        priority = "medium"
    return {
        "success": True,
        "ticket_id": ticket_id,
        "escalated": True,
        "priority": priority,
        "summary": summary,
        "assigned_to": "human-support-queue",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ── Tool registry ─────────────────────────────────────────────────────────────

TOOL_REGISTRY = {
    "get_customer": get_customer,
    "get_order": get_order,
    "get_product": get_product,
    "search_knowledge_base": search_knowledge_base,
    "check_refund_eligibility": check_refund_eligibility,
    "issue_refund": issue_refund,
    "send_reply": send_reply,
    "escalate": escalate,
}

# ── Gemini tool definitions (new google-genai SDK format) ─────────────────────

GEMINI_TOOLS = [
    {
        "name": "get_customer",
        "description": "Look up a customer profile by email. Returns tier, history, and notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Customer email address"}
            },
            "required": ["email"],
        },
    },
    {
        "name": "get_order",
        "description": "Retrieve order details: status, amount, delivery date, return deadline.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID e.g. ORD-1001"}
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_product",
        "description": "Get product metadata: category, warranty period, return window.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID e.g. P001"}
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": "Search ShopWave policy knowledge base for return, refund, warranty info.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query e.g. 'return window electronics'"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_refund_eligibility",
        "description": "Check if an order is eligible for a refund. May occasionally timeout — handle errors.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID to check"}
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "issue_refund",
        "description": "Issue a refund. IRREVERSIBLE. Always call check_refund_eligibility first.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number", "description": "Amount to refund in USD"},
            },
            "required": ["order_id", "amount"],
        },
    },
    {
        "name": "send_reply",
        "description": "Send a reply message to the customer for a given ticket.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "message": {"type": "string", "description": "The reply message to send"},
            },
            "required": ["ticket_id", "message"],
        },
    },
    {
        "name": "escalate",
        "description": "Escalate a ticket to a human agent with summary and priority.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "summary": {"type": "string", "description": "Summary of issue and what was attempted"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
            },
            "required": ["ticket_id", "summary", "priority"],
        },
    },
]


# ── Groq tool definitions (OpenAI-compatible format) ──────────────────────────

GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_customer",
            "description": "Look up a customer profile by email. Returns tier, history, and notes.",
            "parameters": {
                "type": "object",
                "properties": {"email": {"type": "string", "description": "Customer email address"}},
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "Retrieve order details: status, amount, delivery date, return deadline.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "Order ID e.g. ORD-1001"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product",
            "description": "Get product metadata: category, warranty period, return window.",
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "string", "description": "Product ID e.g. P001"}},
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search ShopWave policy knowledge base for return, refund, warranty info.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search query"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_refund_eligibility",
            "description": "Check if an order is eligible for a refund. May occasionally timeout.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "issue_refund",
            "description": "Issue a refund. IRREVERSIBLE. Always call check_refund_eligibility first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "amount": {"type": "number", "description": "Amount to refund in USD"},
                },
                "required": ["order_id", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_reply",
            "description": "Send a reply message to the customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["ticket_id", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate",
            "description": "Escalate ticket to human agent with summary and priority.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "summary": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                },
                "required": ["ticket_id", "summary", "priority"],
            },
        },
    },
]
