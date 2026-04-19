"""
streamlit_app.py — ShopWave Autonomous Support Agent Dashboard
Run: streamlit run streamlit_app.py
"""

import streamlit as st
import asyncio
import json
import os
import time
from pathlib import Path
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ShopWave AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;800&display=swap');

* { font-family: 'Syne', sans-serif; }
code, .mono { font-family: 'JetBrains Mono', monospace !important; }

.stApp { background: #080c14; }

.hero {
    background: linear-gradient(135deg, #0d1f33 0%, #0a1628 50%, #0d1a2e 100%);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(74,158,255,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.hero h1 {
    font-size: 2.4rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0 0 0.5rem 0;
    letter-spacing: -0.5px;
}
.hero p { color: #7a9cc5; font-size: 1.05rem; margin: 0; }
.hero .badge {
    display: inline-block;
    background: rgba(74,158,255,0.15);
    border: 1px solid rgba(74,158,255,0.3);
    color: #4a9eff;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-bottom: 1rem;
    font-family: 'JetBrains Mono', monospace;
}

.metric-card {
    background: #0d1520;
    border: 1px solid #1a2d47;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.metric-card .value {
    font-size: 2.2rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 0.3rem;
}
.metric-card .label {
    font-size: 0.78rem;
    color: #5a7a9a;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-family: 'JetBrains Mono', monospace;
}

.tool-chip {
    display: inline-block;
    background: rgba(74,158,255,0.1);
    border: 1px solid rgba(74,158,255,0.25);
    color: #4a9eff;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    margin: 2px;
    font-family: 'JetBrains Mono', monospace;
}
.tool-chip.write {
    background: rgba(255,100,100,0.1);
    border-color: rgba(255,100,100,0.25);
    color: #ff6464;
}
.tool-chip.action {
    background: rgba(68,204,119,0.1);
    border-color: rgba(68,204,119,0.25);
    color: #44cc77;
}

.ticket-card {
    background: #0d1520;
    border: 1px solid #1a2d47;
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.2s;
}
.ticket-card:hover { border-color: #4a9eff; }

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.7rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.status-refund { background: rgba(68,204,119,0.15); color: #44cc77; border: 1px solid rgba(68,204,119,0.3); }
.status-reply { background: rgba(74,158,255,0.15); color: #4a9eff; border: 1px solid rgba(74,158,255,0.3); }
.status-escalated { background: rgba(204,119,255,0.15); color: #cc77ff; border: 1px solid rgba(204,119,255,0.3); }
.status-error { background: rgba(255,100,100,0.15); color: #ff6464; border: 1px solid rgba(255,100,100,0.3); }

.log-line {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    padding: 0.3rem 0.5rem;
    border-radius: 4px;
    margin: 2px 0;
    background: #060a10;
    color: #7a9cc5;
}
.log-line.tool { color: #4a9eff; }
.log-line.success { color: #44cc77; }
.log-line.error { color: #ff6464; }
.log-line.wait { color: #ffcc44; }

div[data-testid="stSidebar"] { background: #060a10 !important; border-right: 1px solid #1a2d47; }
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_tickets():
    with open(DATA_DIR / "tickets.json") as f:
        return json.load(f)

@st.cache_data
def load_customers():
    with open(DATA_DIR / "customers.json") as f:
        return {c["email"]: c for c in json.load(f)}

def load_audit_log():
    path = Path(__file__).parent / "audit_log.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 1rem 0;'>
        <div style='font-size:1.4rem; font-weight:800; color:#ffffff; margin-bottom:0.3rem;'>🤖 ShopWave</div>
        <div style='font-size:0.75rem; color:#5a7a9a; font-family: JetBrains Mono, monospace;'>AGENTIC AI HACKATHON 2026</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    api_key = st.text_input(
        "GROQ API Key",
        type="password",
        placeholder="gsk_...",
        help="Get a free key at console.groq.com",
        value=os.environ.get("GROQ_API_KEY", "")
    )

    st.divider()
    st.markdown("<div style='font-size:0.75rem; color:#5a7a9a; font-family: JetBrains Mono, monospace;'>BUILT BY</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.9rem; color:#ffffff; font-weight:600;'>Navneeta Mohapatra</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.75rem; color:#5a7a9a;'>Groq + Llama-3.3-70B + Python asyncio</div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🧪 Live Agent", "📊 Audit Dashboard", "🏗️ Architecture"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — LIVE AGENT
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("""
    <div class='hero'>
        <div class='badge'>LIVE DEMO</div>
        <h1>Autonomous Support Agent</h1>
        <p>Submit a ticket and watch the agent reason, call tools, and resolve it in real time.</p>
    </div>
    """, unsafe_allow_html=True)

    # Example tickets
    tickets = load_tickets()
    customers = load_customers()

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown("#### 📨 Submit a Ticket")

        example_options = ["Custom ticket"] + [f"{t['ticket_id']} — {t['subject']}" for t in tickets[:8]]
        selected = st.selectbox("Choose an example or write your own", example_options)

        if selected != "Custom ticket":
            idx = example_options.index(selected) - 1
            default_email = tickets[idx]["customer_email"]
            default_subject = tickets[idx]["subject"]
            default_body = tickets[idx]["body"]
        else:
            default_email = "alice.turner@email.com"
            default_subject = "I need help with my order"
            default_body = "Hi, I have an issue with my recent order ORD-1001. Can you help?"

        email = st.text_input("Customer Email", value=default_email)
        subject = st.text_input("Subject", value=default_subject)
        body = st.text_area("Message", value=default_body, height=120)

        run_btn = st.button("🚀 Run Agent", type="primary", use_container_width=True)

    with col2:
        st.markdown("#### 👤 Customer Profile")
        customer = customers.get(email)
        if customer:
            tier_color = {"vip": "#ffcc44", "premium": "#cc77ff", "standard": "#4a9eff"}.get(customer["tier"], "#4a9eff")
            st.markdown(f"""
            <div class='ticket-card'>
                <div style='font-size:1.1rem; font-weight:700; color:#fff; margin-bottom:0.5rem;'>{customer['name']}</div>
                <div style='margin-bottom:0.3rem;'><span class='status-badge' style='background:rgba(255,204,68,0.1);color:{tier_color};border:1px solid {tier_color}40;'>{customer['tier'].upper()}</span></div>
                <div style='color:#5a7a9a; font-size:0.82rem; margin-top:0.5rem;'>Member since {customer['member_since']}</div>
                <div style='color:#5a7a9a; font-size:0.82rem;'>{customer['total_orders']} orders · ${customer['total_spent']:,.2f} spent</div>
                <div style='color:#7a9cc5; font-size:0.8rem; margin-top:0.5rem; font-style:italic;'>{customer.get('notes','')}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Enter a valid customer email to see profile")

    # ── Run agent ──────────────────────────────────────────────────────────────
    if run_btn:
        if not api_key:
            st.error("⚠️ Please enter your GROQ API KEY in the sidebar first!")
        else:
            os.environ["GROQ_API_KEY"] = api_key

            ticket = {
                "ticket_id": "DEMO-001",
                "customer_email": email,
                "subject": subject,
                "body": body,
            }

            st.divider()
            st.markdown("#### ⚙️ Agent Execution Trace")

            log_container = st.container()
            result_container = st.container()

            logs = []
            tool_calls_made = []

            with log_container:
                log_placeholder = st.empty()

                def render_logs():
                    html = ""
                    for log in logs:
                        cls = "tool" if "→" in log else ("success" if "✅" in log else ("error" if "❌" in log else ("wait" if "⏳" in log else "")))
                        html += f"<div class='log-line {cls}'>{log}</div>"
                    log_placeholder.markdown(html, unsafe_allow_html=True)

                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Starting agent for ticket: {subject}")
                render_logs()

            # Import and run agent
            try:
                import sys
                sys.path.insert(0, str(Path(__file__).parent))
                from agent import process_ticket
                from audit import AuditLogger

                audit_logger = AuditLogger()

                # Monkey-patch to capture logs
                import tools as tools_module
                original_registry = dict(tools_module.TOOL_REGISTRY)

                async def run_with_logging():
                    from groq import Groq
                    from agent import MAX_TOOL_RETRIES, MAX_AGENT_ITERATIONS, SYSTEM_PROMPT, GROQ_TOOLS, _execute_tool
                    import json as json_mod

                    client = Groq(api_key=api_key)
                    audit = audit_logger.start("DEMO-001", subject, email)

                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Ticket ID: DEMO-001\nFrom: {email}\nSubject: {subject}\n\nMessage:\n{body}\n\nPlease resolve this ticket fully."}
                    ]

                    final_action = "unknown"
                    outcome_summary = ""

                    for iteration in range(MAX_AGENT_ITERATIONS):
                        response = await asyncio.to_thread(
                            client.chat.completions.create,
                            model="llama-3.3-70b-versatile",
                            messages=messages,
                            tools=GROQ_TOOLS,
                            tool_choice="auto",
                            max_tokens=2048,
                        )
                        msg = response.choices[0].message
                        messages.append(msg)

                        if not msg.tool_calls:
                            break

                        for tool_call in msg.tool_calls:
                            tool_name = tool_call.function.name
                            try:
                                tool_input = json_mod.loads(tool_call.function.arguments)
                            except:
                                tool_input = {}

                            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}]  → {tool_name}({', '.join(f'{k}={repr(v)[:20]}' for k,v in tool_input.items())})")
                            render_logs()
                            tool_calls_made.append(tool_name)

                            result_str = await _execute_tool(tool_name, tool_input, audit)

                            if tool_name == "issue_refund":
                                final_action = "refund_issued"
                                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Refund issued!")
                            elif tool_name == "send_reply":
                                if final_action != "refund_issued":
                                    final_action = "reply_sent"
                                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Reply sent to customer")
                            elif tool_name == "escalate":
                                final_action = "escalated"
                                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🔼 Ticket escalated to human agent")

                            render_logs()

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result_str,
                            })

                    audit.complete(final_action, "Demo run completed")
                    return final_action, audit

                with st.spinner("Agent reasoning..."):
                    final_action, audit = asyncio.run(run_with_logging())

                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Agent completed — {len(tool_calls_made)} tool calls made")
                render_logs()

                # Result summary
                st.divider()
                col_r1, col_r2, col_r3 = st.columns(3)
                with col_r1:
                    action_map = {
                        "refund_issued": ("✅ Refund Issued", "status-refund"),
                        "reply_sent": ("💬 Reply Sent", "status-reply"),
                        "escalated": ("🔼 Escalated", "status-escalated"),
                    }
                    label, cls = action_map.get(final_action, ("❓ Unknown", "status-error"))
                    st.markdown(f"<div class='metric-card'><div class='value' style='font-size:1.2rem;'><span class='status-badge {cls}'>{label}</span></div><div class='label'>Final Action</div></div>", unsafe_allow_html=True)
                with col_r2:
                    st.markdown(f"<div class='metric-card'><div class='value' style='color:#4a9eff;'>{len(tool_calls_made)}</div><div class='label'>Tool Calls Made</div></div>", unsafe_allow_html=True)
                with col_r3:
                    st.markdown(f"<div class='metric-card'><div class='value' style='color:#44cc77;'>{'≥3 ✓' if len(tool_calls_made) >= 3 else '<3 ✗'}</div><div class='label'>Min Chain Met</div></div>", unsafe_allow_html=True)

                # Tool call chain
                st.markdown("#### 🔧 Tool Call Chain")
                chips = ""
                read_tools = {"get_customer", "get_order", "get_product", "search_knowledge_base"}
                write_tools = {"issue_refund", "check_refund_eligibility"}
                for t in tool_calls_made:
                    cls = "write" if t in write_tools else ("action" if t in {"send_reply", "escalate"} else "")
                    chips += f"<span class='tool-chip {cls}'>{t}</span>"
                st.markdown(chips, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Make sure your GROQ_API_KEY is set correctly in the sidebar.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — AUDIT DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("""
    <div class='hero'>
        <div class='badge'>AUDIT LOG</div>
        <h1>20-Ticket Processing Report</h1>
        <p>Full audit trail showing tool calls, reasoning, and outcomes for all tickets.</p>
    </div>
    """, unsafe_allow_html=True)

    audit_data = load_audit_log()

    if not audit_data:
        st.warning("No audit_log.json found. Run `python main.py` first to generate it.")
    else:
        # Summary metrics
        total = len(audit_data)
        outcomes = {}
        for r in audit_data.values():
            a = r.get("final_action", "unknown")
            outcomes[a] = outcomes.get(a, 0) + 1

        cols = st.columns(5)
        metrics = [
            (str(total), "Total Tickets", "#4a9eff"),
            (str(outcomes.get("refund_issued", 0)), "Refunds Issued", "#44cc77"),
            (str(outcomes.get("reply_sent", 0)), "Replies Sent", "#4a9eff"),
            (str(outcomes.get("escalated", 0)), "Escalated", "#cc77ff"),
            (str(outcomes.get("error", 0)), "Errors", "#ff6464"),
        ]
        for col, (val, label, color) in zip(cols, metrics):
            with col:
                st.markdown(f"<div class='metric-card'><div class='value' style='color:{color};'>{val}</div><div class='label'>{label}</div></div>", unsafe_allow_html=True)

        st.divider()

        # Ticket list
        st.markdown("#### 🎫 All Tickets")
        for tid, record in audit_data.items():
            action = record.get("final_action", "unknown")
            icon = {"refund_issued": "✅", "reply_sent": "💬", "escalated": "🔼", "error": "❌"}.get(action, "❓")
            cls = {"refund_issued": "status-refund", "reply_sent": "status-reply", "escalated": "status-escalated", "error": "status-error"}.get(action, "")
            tools_used = [t["tool_name"] for t in record.get("tool_calls", [])]

            with st.expander(f"{icon} {tid} — {record.get('subject', '')}"):
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.markdown(f"<span class='status-badge {cls}'>{action}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Email:** `{record.get('customer_email','')}`")
                    st.markdown(f"**Tools used:** {len(tools_used)}")
                with col_b:
                    st.markdown("**Tool call chain:**")
                    chips = ""
                    for t in tools_used:
                        cls2 = "write" if t in {"issue_refund","check_refund_eligibility"} else ("action" if t in {"send_reply","escalate"} else "")
                        chips += f"<span class='tool-chip {cls2}'>{t}</span>"
                    st.markdown(chips or "_No tool calls_", unsafe_allow_html=True)
                    st.markdown(f"**Summary:** {record.get('outcome_summary','—')}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div class='hero'>
        <div class='badge'>SYSTEM DESIGN</div>
        <h1>Agent Architecture</h1>
        <p>Agentic loop design, tool layer, concurrency model, and error handling strategy.</p>
    </div>
    """, unsafe_allow_html=True)

    arch_path = Path(__file__).parent / "architecture.png"
    if arch_path.exists():
        st.image(str(arch_path), use_container_width=True)
    else:
        st.warning("architecture.png not found in project directory.")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🔧 Tool Layer")
        tools_info = [
            ("get_customer", "READ", "Look up customer profile + tier"),
            ("get_order", "READ", "Order status, return deadline"),
            ("get_product", "READ", "Category, warranty, returnability"),
            ("search_knowledge_base", "READ", "Policy & FAQ semantic search"),
            ("check_refund_eligibility", "CHECK", "Eligibility gate — may timeout (20%)"),
            ("issue_refund", "WRITE ⚠️", "Irreversible — always gated"),
            ("send_reply", "ACTION", "Customer-facing message"),
            ("escalate", "ACTION", "Human handoff with context"),
        ]
        for name, type_, desc in tools_info:
            color = "#ff6464" if "WRITE" in type_ else ("#ffcc44" if "CHECK" in type_ else ("#44cc77" if "ACTION" in type_ else "#4a9eff"))
            st.markdown(f"""
            <div class='ticket-card' style='padding:0.7rem 1rem; margin-bottom:0.4rem;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <span style='font-family: JetBrains Mono, monospace; color:#fff; font-size:0.85rem;'>{name}</span>
                    <span style='font-size:0.68rem; color:{color}; font-family: JetBrains Mono, monospace;'>{type_}</span>
                </div>
                <div style='color:#5a7a9a; font-size:0.78rem; margin-top:0.2rem;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### 🛡️ Error Handling")
        failures = [
            ("Tool Timeout", "Retry x2 with backoff → escalate", "#ff9944"),
            ("Malformed Tool Args", "try/except JSON → log + skip", "#ffcc44"),
            ("Expired Return Window", "Check VIP leniency → escalate if needed", "#cc77ff"),
            ("Refund > $200", "Mandatory escalation — no auto-refund", "#ff6464"),
            ("Rate Limit 429", "Logged in audit — 15s gap between tickets", "#4a9eff"),
        ]
        for title, desc, color in failures:
            st.markdown(f"""
            <div class='ticket-card' style='padding:0.7rem 1rem; margin-bottom:0.4rem; border-color:{color}40;'>
                <div style='color:{color}; font-weight:700; font-size:0.85rem; margin-bottom:0.2rem;'>{title}</div>
                <div style='color:#7a9cc5; font-size:0.78rem;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("#### ⚡ Tech Stack")
        stack = [
            ("LLM", "Llama-3.3-70B via Groq"),
            ("Concurrency", "asyncio — sequential with 15s gap"),
            ("Error Recovery", "Retry + escalate fallback"),
            ("Audit", "Full JSON trace per ticket"),
            ("Tools", "8 mock tools backed by JSON data"),
        ]
        for k, v in stack:
            st.markdown(f"""
            <div style='display:flex; justify-content:space-between; padding:0.4rem 0; border-bottom:1px solid #1a2d47;'>
                <span style='color:#5a7a9a; font-size:0.82rem; font-family: JetBrains Mono, monospace;'>{k}</span>
                <span style='color:#ffffff; font-size:0.82rem;'>{v}</span>
            </div>
            """, unsafe_allow_html=True)
