"""
╔══════════════════════════════════════════════════════════════════════════╗
║          CHART-ON-THE-FLY KPI AGENT  –  app.py                         ║
║  Real agentic loop: OpenRouter → Gemini Flash → chart tools → Plotly   ║
║                                                                          ║
║  Flow per user message:                                                  ║
║   User prompt → Gemini (function-calling) → tool executor               ║
║              → results fed back → Gemini final text → Streamlit render  ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# ── Standard library ──────────────────────────────────────────────────────────
import json
import os
import random
from datetime import datetime, timedelta

# ── Third-party ───────────────────────────────────────────────────────────────
import pandas as pd
import streamlit as st
from openai import OpenAI

# ── Local tools module ────────────────────────────────────────────────────────
from tools import TOOL_SCHEMAS, execute_tool

# ── Load .env (API key) if available ─────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG  (must be the first Streamlit call)
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Chart Agent · KPI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM DARK-MODE CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        /* ── App background ── */
        .stApp {
            background: linear-gradient(135deg, #0a0c18 0%, #0f1623 50%, #0a1018 100%);
            min-height: 100vh;
        }
        .block-container { padding-top: 2rem; padding-bottom: 4rem; }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f1623 0%, #0a1018 100%);
            border-right: 1px solid rgba(99,179,237,0.12);
        }
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] caption { color: #64748b !important; }

        /* ── Chat messages ── */
        [data-testid="stChatMessage"] {
            background: rgba(255,255,255,0.025);
            border: 1px solid rgba(99,179,237,0.10);
            border-radius: 18px;
            padding: 1.1rem 1.3rem;
            margin-bottom: 0.8rem;
            backdrop-filter: blur(12px);
        }

        /* ── Metric cards ── */
        [data-testid="stMetric"] {
            background: rgba(99,179,237,0.055);
            border: 1px solid rgba(99,179,237,0.18);
            border-radius: 14px;
            padding: 1.2rem 1rem;
            text-align: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 28px rgba(99,179,237,0.16);
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.75rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: #63b3ed !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.95rem !important;
            font-weight: 700 !important;
            color: #f1f5f9 !important;
        }
        [data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

        /* ── Chat input ── */
        [data-testid="stChatInput"] {
            border: 1.5px solid rgba(99,179,237,0.3) !important;
            border-radius: 14px !important;
            background: rgba(255,255,255,0.03) !important;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: #63b3ed !important;
            box-shadow: 0 0 0 3px rgba(99,179,237,0.13) !important;
        }

        /* ── Page title gradient ── */
        h1 {
            background: linear-gradient(90deg, #63b3ed 0%, #a78bfa 60%, #68d391 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.3rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.025em;
        }

        /* ── Section heading colours ── */
        h2, h3 { color: #e2e8f0 !important; }

        /* ── Dividers ── */
        hr { border-color: rgba(99,179,237,0.12) !important; }

        /* ── Plotly chart wrapper ── */
        [data-testid="stPlotlyChart"] {
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid rgba(99,179,237,0.12);
            background: rgba(255,255,255,0.015);
        }

        /* ── Sidebar dataframe ── */
        [data-testid="stDataFrame"] {
            border: 1px solid rgba(99,179,237,0.12);
            border-radius: 10px;
            overflow: hidden;
        }

        /* ── Badges ── */
        .agent-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            background: rgba(99,179,237,0.10);
            border: 1px solid rgba(99,179,237,0.25);
            border-radius: 999px;
            padding: 0.2rem 0.9rem;
            font-size: 0.72rem;
            font-weight: 600;
            color: #63b3ed;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.6rem;
        }
        .tool-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            background: rgba(167,139,250,0.10);
            border: 1px solid rgba(167,139,250,0.22);
            border-radius: 999px;
            padding: 0.15rem 0.75rem;
            font-size: 0.68rem;
            font-weight: 600;
            color: #a78bfa;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-right: 0.35rem;
        }

        /* ── Scrollbar ── */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb {
            background: rgba(99,179,237,0.22);
            border-radius: 999px;
        }

        /* ── Spinner text ── */
        .stSpinner > div { color: #63b3ed !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# DATA LAYER  –  1 000-row mock sales dataset (cached)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def generate_mock_data() -> pd.DataFrame:
    """Simulate a CRM / database export. Swap with pd.read_sql() in production."""
    random.seed(42)
    REGIONS    = ["North", "South", "East", "West", "EMEA"]
    PRODUCTS   = ["Enterprise License", "Cloud Storage", "Consulting", "Support SLA"]
    STATUSES   = ["Won", "Lost", "Pending"]
    STATUS_WTS = [0.35, 0.40, 0.25]
    today      = datetime.now()

    rows = []
    for _ in range(1_000):
        rows.append({
            "Date":      today - timedelta(days=random.randint(0, 89)),
            "Region":    random.choice(REGIONS),
            "Product":   random.choice(PRODUCTS),
            "DealValue": random.randint(5_000, 150_000),
            "Status":    random.choices(STATUSES, weights=STATUS_WTS, k=1)[0],
        })

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df


df = generate_mock_data()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR  –  data preview + API key input
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        "<h2 style='color:#63b3ed; font-size:1.05rem; margin-bottom:0.2rem;'>"
        "⚙️ Backend Data Layer</h2>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Raw dataset the agent reads from. "
        "In production, replace with a live SQL / API connection."
    )
    st.divider()

    st.markdown(
        "<span style='font-size:0.72rem; font-weight:600; color:#63b3ed; "
        "text-transform:uppercase; letter-spacing:0.06em;'>📄 Preview – first 15 rows</span>",
        unsafe_allow_html=True,
    )
    st.dataframe(df.head(15), use_container_width=True, hide_index=True)
    st.divider()

    st.markdown(f"**Records:** `{len(df):,}` rows")
    st.markdown("**Columns**")
    for col, dtype in df.dtypes.items():
        st.markdown(f"- `{col}` — *{dtype}*")
    st.divider()

    # ── API key override (sidebar input takes precedence over .env) ──────────
    st.markdown(
        "<span style='font-size:0.72rem; font-weight:600; color:#a78bfa; "
        "text-transform:uppercase; letter-spacing:0.06em;'>🔑 OpenRouter API Key</span>",
        unsafe_allow_html=True,
    )
    sidebar_key = st.text_input(
        "API Key",
        value="",
        type="password",
        placeholder="sk-or-v1-…  (overrides .env)",
        label_visibility="collapsed",
    )
    st.caption("Leave blank to use the key from `.env` / environment variable.")
    st.divider()
    st.caption("🔒 Data is generated locally. Charts powered by Plotly + Gemini Flash.")


# ── Resolve the active API key ────────────────────────────────────────────────
# ── Resolve API key: st.secrets (Cloud) → env var (local) → sidebar input ──
def _get_api_key() -> str:
    # 1. Streamlit Community Cloud secrets (TOML)
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    # 2. Environment variable / .env file
    env_key = os.getenv("OPENROUTER_API_KEY", "")
    if env_key:
        return env_key
    # 3. Sidebar manual input (dev fallback)
    return sidebar_key.strip()

OPENROUTER_API_KEY = _get_api_key()

# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT  –  tells Gemini what data it has and how to behave
# ══════════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """You are an intelligent Sales KPI Chart Agent with access to a sales dataset.

Dataset (1,000 records, last 90 days):
  - Date      : sale date
  - Region    : North | South | East | West | EMEA
  - Product   : Enterprise License | Cloud Storage | Consulting | Support SLA
  - DealValue : deal amount in USD ($5,000 – $150,000)
  - Status    : Won | Lost | Pending

Your job is to answer data questions by calling the appropriate chart tools.
Rules:
1. ALWAYS use a tool when the user asks about data, charts, trends, KPIs, or comparisons.
2. Pick the best chart type for the question (line for trends, pie for proportions, bar for comparisons, scatter for distributions, kpi_summary for numeric KPIs).
3. Apply the correct filters (filter_region, filter_status) when the user mentions a specific region or status.
4. You may call multiple tools in one response if it helps (e.g. KPIs + a chart).
5. After the tools return, write a short, insightful analysis (2–4 sentences) in plain language.
6. Be concise and data-driven. Do not make up numbers — rely on tool results.
"""

# ══════════════════════════════════════════════════════════════════════════════
# AGENTIC LOOP
# ══════════════════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────────────────────
# Helper: human-readable tool call descriptions for the status log
# ──────────────────────────────────────────────────────────────────────────────

def _describe_tool_call(tool_name: str, args: dict) -> str:
    """Return a concise plain-English description of what a tool call is doing."""
    region = args.get("filter_region") or "all"
    status = args.get("filter_status") or "all"
    region_str = "all regions" if region == "all" else f"{region} region"
    status_str = "" if status == "all" else f" · {status} deals only"

    if tool_name == "bar_chart":
        y     = "Revenue" if args.get("y_col") == "DealValue" else "Deal count"
        x     = args.get("x_col", "?")
        grp   = args.get("group_by") or "none"
        grp_s = f", grouped by {grp}" if grp != "none" else ""
        return f"{y} by {x}{grp_s} — {region_str}{status_str}"

    if tool_name == "line_chart":
        y     = "Revenue" if args.get("y_col") == "DealValue" else "Deal count"
        grp   = args.get("group_by") or "none"
        grp_s = f" per {grp}" if grp != "none" else ""
        return f"Weekly {y} trend{grp_s} — {region_str}{status_str}"

    if tool_name == "pie_chart":
        val   = "Revenue share" if args.get("value_col") == "DealValue" else "Deal share"
        label = args.get("label_col", "?")
        return f"{val} by {label} — {region_str}{status_str}"

    if tool_name == "scatter_chart":
        color = args.get("color_col") or "Region"
        return f"Deal values over time, coloured by {color} — {region_str}{status_str}"

    if tool_name == "kpi_summary":
        return f"KPI metrics for {region_str}"

    return tool_name


def run_agent(
    user_prompt: str,
    history: list,
    df: pd.DataFrame,
    api_key: str,
    status_container=None,   # optional st.status() context for live updates
):
    """
    Send the user prompt to Gemini Flash via OpenRouter with function-calling.
    Executes tool calls, feeds results back, and returns the agent's final response.

    Returns
    -------
    final_text      : str
    charts          : list of (tool_name: str, plotly_fig)
    kpi_data        : list of dict  (from kpi_summary calls)
    tool_calls_made : list of str   (tool names called, for badge display)
    tool_summaries  : list of str   (raw tool output text — ground truth for verifier)
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://localhost/kpi-agent",
            "X-Title": "KPI Chart Agent",
        },
    )

    # Build messages: system + rolling history + new user turn
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})

    charts: list          = []
    kpi_data: list        = []
    tool_calls_made: list = []
    tool_summaries: list  = []   # ← ground truth collected for the verifier

    def _status(msg: str):
        """Write a line to the status container if one was provided."""
        if status_container is not None:
            status_container.write(msg)

    _status("🧠 **Understanding your question...**")

    # ── Agentic loop (max 4 iterations to avoid runaway calls) ───────────────
    for _ in range(4):
        response = client.chat.completions.create(
            model="google/gemini-3.1-flash-lite",
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.2,
        )

        choice = response.choices[0]

        # ── The model wants to call tools ────────────────────────────────────
        if choice.finish_reason == "tool_calls":
            assistant_msg = choice.message
            messages.append(assistant_msg)

            for tc in assistant_msg.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments)
                tool_calls_made.append(tool_name)

                desc = _describe_tool_call(tool_name, tool_args)
                _status(f"🔧 **Selected tool:** `{tool_name}`  \n&nbsp;&nbsp;&nbsp;&nbsp;↳ {desc}")

                fig, summary, extras = execute_tool(tool_name, tool_args, df)
                tool_summaries.append(f"[{tool_name}] {summary}")

                _status(f"&nbsp;&nbsp;&nbsp;&nbsp;✓ {summary}")

                if fig is not None:
                    charts.append((tool_name, fig))
                if extras is not None:
                    kpi_data.append(extras)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": summary,
                })

        # ── Final text response ───────────────────────────────────────────────
        else:
            _status("📝 **Writing analysis...**")
            final_text = choice.message.content or ""
            return final_text, charts, kpi_data, tool_calls_made, tool_summaries

    return "I've generated the charts above.", charts, kpi_data, tool_calls_made, tool_summaries


# ══════════════════════════════════════════════════════════════════════════════
# VERIFIER  –  LLM-as-judge: checks the agent's written claims against
#              the actual tool outputs (ground truth)
# ══════════════════════════════════════════════════════════════════════════════

def verify_response(final_text: str, tool_summaries: list, api_key: str) -> dict | None:
    """
    Run a fast verification pass comparing the agent's written analysis against
    the exact numbers returned by the tools.

    Returns a dict: {verdict, confidence, notes} or None if nothing to verify.
    """
    if not tool_summaries or not final_text.strip():
        return None

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://localhost/kpi-agent",
            "X-Title": "KPI Chart Agent Verifier",
        },
    )

    ground_truth = "\n".join(f"  • {s}" for s in tool_summaries)

    try:
        response = client.chat.completions.create(
            model="google/gemini-3.1-flash-lite",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a fact-checker for an AI data analytics agent. "
                        "Compare the agent's written response against the tool output data (ground truth). "
                        "Check if any numbers, percentages, region names, or factual claims "
                        "in the response contradict or are absent from the tool outputs. "
                        "Minor rounding or rephrasing is acceptable. "
                        "Respond ONLY with valid JSON — no markdown, no extra text:\n"
                        '{"verdict": "accurate" | "minor_issues" | "significant_issues", '
                        '"confidence": <integer 0-100>, '
                        '"notes": "<one concise sentence>"}'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Tool outputs (ground truth):\n{ground_truth}\n\n"
                        f"Agent's written response:\n{final_text}"
                    ),
                },
            ],
            temperature=0.0,
            max_tokens=120,
        )
        raw = response.choices[0].message.content.strip()
        # Strip accidental markdown fences
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        return json.loads(raw)
    except Exception:
        return {"verdict": "unknown", "confidence": 0, "notes": "Verification could not be completed."}


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE  –  dual-track history
# ══════════════════════════════════════════════════════════════════════════════
#
# `api_messages`   – text-only history sent to the LLM (no Plotly figs)
# `display_history` – full display items including charts, metric cards
#

_WELCOME = (
    "👋 Hello! I'm your **Chart-on-the-Fly KPI Agent** powered by **Gemini Flash** via OpenRouter.\n\n"
    "I have access to **1,000 sales records** across 5 regions and 4 products.\n\n"
    "Ask me anything — I'll pick the right chart automatically:\n"
    "- *\"Show me a revenue trend over time for EMEA\"* → 📈 line chart\n"
    "- *\"Pie chart of deal status for the West region\"* → 🥧 donut chart\n"
    "- *\"Compare revenue by product across all regions\"* → 📊 bar chart\n"
    "- *\"KPIs for North\"* → 🎯 metric cards\n"
    "- *\"Scatter of deal values coloured by product\"* → 🔵 scatter plot\n\n"
    "**Regions:** North · South · East · West · EMEA  \n"
    "**Products:** Enterprise License · Cloud Storage · Consulting · Support SLA"
)

if "api_messages" not in st.session_state:
    st.session_state.api_messages = []

if "display_history" not in st.session_state:
    st.session_state.display_history = [
        {"role": "assistant", "elements": [{"type": "text", "data": _WELCOME}]}
    ]

# ══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h1>📊 Chart-on-the-Fly Agent</h1>"
    "<p style='color:#475569; margin-top:-0.5rem; margin-bottom:1.5rem; font-size:0.9rem;'>"
    "Powered by Gemini 3.1 Flash Lite · OpenRouter · Plotly · Streamlit"
    "</p>",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# RENDER HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def render_kpi_cards(metrics: dict):
    """Render four metric cards from a kpi_summary result."""
    region_label = (
        "All Regions" if metrics["region"] == "all"
        else f"{metrics['region']} Region"
    )
    st.markdown(
        f"<span class='agent-badge'>🎯 KPI Summary — {region_label}</span>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            "💰 Revenue (Won)",
            f"${metrics['total_revenue']:,}",
            f"avg ${metrics['avg_deal_size']:,} / deal",
        )
    with c2:
        st.metric(
            "🏆 Win Rate",
            f"{metrics['win_rate']}%",
            f"{metrics['won_deals']} won · {metrics['lost_deals']} lost",
        )
    with c3:
        st.metric(
            "⏳ Pipeline",
            f"{metrics['pending_deals']} deals",
            f"Total reviewed: {metrics['total_deals']}",
        )
    with c4:
        st.metric(
            "📋 Total Deals",
            f"{metrics['total_deals']}",
            f"Won {metrics['won_deals']} / Lost {metrics['lost_deals']}",
        )


def render_display_item(item: dict):
    """Render a single display history item inside st.chat_message."""
    for el in item["elements"]:
        if el["type"] == "text":
            st.markdown(el["data"])
        elif el["type"] == "chart":
            st.plotly_chart(
                el["data"],
                use_container_width=True,
                config={"displayModeBar": True, "displaylogo": False},
            )
        elif el["type"] == "kpi":
            render_kpi_cards(el["data"])
        elif el["type"] == "tool_badges":
            badges_html = "".join(
                f"<span class='tool-badge'>🔧 {t}</span>" for t in el["data"]
            )
            st.markdown(badges_html, unsafe_allow_html=True)
        elif el["type"] == "verification":
            v = el["data"]
            verdict   = v.get("verdict", "unknown")
            confidence = v.get("confidence", 0)
            notes     = v.get("notes", "")
            icon, colour, label = {
                "accurate":            ("✅", "#22c55e", "Verified accurate"),
                "minor_issues":        ("⚠️", "#f59e0b", "Minor issues"),
                "significant_issues":  ("❌", "#ef4444", "Significant issues"),
            }.get(verdict, ("❓", "#94a3b8", "Verification unknown"))
            st.markdown(
                f"""
                <div style='
                    display:inline-flex; align-items:flex-start; gap:0.6rem;
                    background:rgba(255,255,255,0.03);
                    border:1px solid {colour}44;
                    border-left: 3px solid {colour};
                    border-radius:10px;
                    padding:0.6rem 0.9rem;
                    margin-top:0.5rem;
                    font-size:0.8rem;
                    line-height:1.5;
                    max-width:600px;
                '>
                    <span style='font-size:1rem;flex-shrink:0'>{icon}</span>
                    <div>
                        <span style='font-weight:700; color:{colour};'>{label}</span>
                        <span style='color:rgba(255,255,255,0.3); margin-left:0.5rem;'>({confidence}% confidence)</span><br>
                        <span style='color:rgba(255,255,255,0.5);'>{notes}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# RENDER HISTORY
# ══════════════════════════════════════════════════════════════════════════════
for item in st.session_state.display_history:
    with st.chat_message(item["role"]):
        render_display_item(item)

# ══════════════════════════════════════════════════════════════════════════════
# CHAT INPUT  +  AGENT INVOCATION
# ══════════════════════════════════════════════════════════════════════════════
user_prompt = st.chat_input("Ask me to chart anything…  e.g. 'Revenue trend for EMEA by product'")

if user_prompt:
    # ── Guard: API key required ───────────────────────────────────────────────
    if not OPENROUTER_API_KEY:
        st.error(
            "⚠️ No API key found. Add your OpenRouter key to `.env` as "
            "`OPENROUTER_API_KEY` or paste it in the sidebar."
        )
        st.stop()

    # ── Show user message ─────────────────────────────────────────────────────
    st.session_state.display_history.append(
        {"role": "user", "elements": [{"type": "text", "data": user_prompt}]}
    )
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # ── Call the agent with a live status log ─────────────────────────────────
    with st.chat_message("assistant"):
        with st.status("🤖 Agent working...", expanded=True) as status:
            try:
                final_text, charts, kpi_data_list, tool_names, tool_summaries = run_agent(
                    user_prompt,
                    st.session_state.api_messages,
                    df,
                    OPENROUTER_API_KEY,
                    status_container=status,
                )
                error_occurred = False
            except Exception as exc:
                final_text     = f"⚠️ Agent error: `{exc}`"
                charts         = []
                kpi_data_list  = []
                tool_names     = []
                tool_summaries = []
                error_occurred = True

            # Run verifier inside the same status block
            if not error_occurred and tool_summaries:
                status.write("🔍 **Verifying accuracy...**")
                verification = verify_response(final_text, tool_summaries, OPENROUTER_API_KEY)
            else:
                verification = None

            # Collapse with a final summary label
            if error_occurred:
                status.update(label="❌ Agent encountered an error", state="error", expanded=True)
            elif verification and verification.get("verdict") == "significant_issues":
                status.update(label="⚠️ Done — accuracy issues flagged", state="complete", expanded=False)
            else:
                status.update(label="✅ Done", state="complete", expanded=False)

        # ── Assemble and render display elements ──────────────────────────────
        display_elements = []

        # 1. Tool badges
        if tool_names:
            badges_html = "".join(
                f"<span class='tool-badge'>🔧 {t}</span>" for t in tool_names
            )
            st.markdown(badges_html, unsafe_allow_html=True)
            display_elements.append({"type": "tool_badges", "data": tool_names})

        # 2. KPI metric cards
        for metrics in kpi_data_list:
            render_kpi_cards(metrics)
            display_elements.append({"type": "kpi", "data": metrics})

        # 3. Charts
        for tool_name, fig in charts:
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": True, "displaylogo": False},
            )
            display_elements.append({"type": "chart", "data": fig})

        # 4. Agent's written analysis
        if final_text:
            st.markdown(final_text)
            display_elements.append({"type": "text", "data": final_text})

        # 5. Verification badge
        if verification:
            v          = verification
            verdict    = v.get("verdict", "unknown")
            confidence = v.get("confidence", 0)
            notes      = v.get("notes", "")
            icon, colour, label = {
                "accurate":           ("✅", "#22c55e", "Verified accurate"),
                "minor_issues":       ("⚠️", "#f59e0b", "Minor issues"),
                "significant_issues": ("❌", "#ef4444", "Significant issues"),
            }.get(verdict, ("❓", "#94a3b8", "Verification unknown"))
            st.markdown(
                f"""
                <div style='
                    display:inline-flex; align-items:flex-start; gap:0.6rem;
                    background:rgba(255,255,255,0.03);
                    border:1px solid {colour}44;
                    border-left:3px solid {colour};
                    border-radius:10px;
                    padding:0.6rem 0.9rem;
                    margin-top:0.5rem;
                    font-size:0.8rem;
                    line-height:1.5;
                    max-width:620px;
                '>
                    <span style='font-size:1rem;flex-shrink:0'>{icon}</span>
                    <div>
                        <span style='font-weight:700;color:{colour};'>{label}</span>
                        <span style='color:rgba(255,255,255,0.3);margin-left:0.5rem;'>({confidence}% confidence)</span><br>
                        <span style='color:rgba(255,255,255,0.5);'>{notes}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            display_elements.append({"type": "verification", "data": verification})

    # ── Persist to session state ──────────────────────────────────────────────
    st.session_state.display_history.append(
        {"role": "assistant", "elements": display_elements}
    )

    # Update rolling API history (text only – no Plotly figs)
    st.session_state.api_messages.append({"role": "user",      "content": user_prompt})
    st.session_state.api_messages.append({"role": "assistant", "content": final_text or ""})

    # Keep API history bounded (last 20 turns = 40 messages)
    if len(st.session_state.api_messages) > 40:
        st.session_state.api_messages = st.session_state.api_messages[-40:]
