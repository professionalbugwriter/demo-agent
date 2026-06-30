"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         OSS SALES KPI AGENT SWARM  –  app.py                               ║
║  Local, open-source alternative to Microsoft Copilot Studio                 ║
║                                                                              ║
║  A 6-agent swarm simulating a real-world multi-agent AI pipeline:           ║
║                                                                              ║
║  User Prompt                                                                 ║
║       │                                                                      ║
║  [SwarmOrchestrator]  ← coordinates all agents via shared AgentBus          ║
║       ├─► 🔍 IntentAgent    – LLM: entity + query-type extraction           ║
║       ├─► 🗄️  DataAgent      – Python: filter & enrich DataFrame             ║
║       ├─► 📐 KPIAgent       – Python: compute KPI metrics                   ║
║       ├─► 📊 VizAgent       – LLM: pick + execute chart tools               ║
║       ├─► 📝 NarratorAgent  – LLM: write grounded insight summary           ║
║       └─► ✅ VerifierAgent  – LLM: fact-check narrative vs. data            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ── Standard library ───────────────────────────────────────────────────────────
import json
import os
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

# ── Third-party ────────────────────────────────────────────────────────────────
import pandas as pd
import streamlit as st
from openai import OpenAI

# ── Local tools module ─────────────────────────────────────────────────────────
from tools import TOOL_SCHEMAS, execute_tool

# ── Load .env if available ─────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG  (must be the very first Streamlit call)
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="KPI Agent Swarm",
    page_icon="🐝",
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

        /* ── Page title ── */
        h1 {
            background: linear-gradient(90deg, #63b3ed 0%, #a78bfa 60%, #68d391 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.3rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.025em;
        }
        h2, h3 { color: #e2e8f0 !important; }
        hr { border-color: rgba(99,179,237,0.12) !important; }

        /* ── Chart wrapper ── */
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

        /* ── Tool / agent badges ── */
        .agent-badge {
            display: inline-flex; align-items: center; gap: 0.35rem;
            background: rgba(99,179,237,0.10); border: 1px solid rgba(99,179,237,0.25);
            border-radius: 999px; padding: 0.2rem 0.9rem;
            font-size: 0.72rem; font-weight: 600; color: #63b3ed;
            letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.6rem;
        }
        .tool-badge {
            display: inline-flex; align-items: center; gap: 0.3rem;
            background: rgba(167,139,250,0.10); border: 1px solid rgba(167,139,250,0.22);
            border-radius: 999px; padding: 0.15rem 0.75rem;
            font-size: 0.68rem; font-weight: 600; color: #a78bfa;
            letter-spacing: 0.05em; text-transform: uppercase; margin-right: 0.35rem;
        }
        .swarm-badge {
            display: inline-flex; align-items: center; gap: 0.3rem;
            background: rgba(104,211,145,0.10); border: 1px solid rgba(104,211,145,0.22);
            border-radius: 999px; padding: 0.15rem 0.75rem;
            font-size: 0.68rem; font-weight: 600; color: #68d391;
            letter-spacing: 0.05em; text-transform: uppercase; margin-right: 0.35rem;
        }

        /* ── Intent card ── */
        .intent-card {
            background: rgba(167,139,250,0.06);
            border: 1px solid rgba(167,139,250,0.18);
            border-radius: 10px; padding: 0.65rem 0.9rem;
            margin-top: 0.4rem; font-size: 0.8rem;
            color: #94a3b8; line-height: 1.7;
        }
        .intent-lbl {
            color: #a78bfa; font-weight: 600;
            font-size: 0.71rem; text-transform: uppercase; letter-spacing: 0.06em;
        }

        /* ── Swarm Monitor rows ── */
        .sm-row {
            display: flex; align-items: center; gap: 0.55rem;
            padding: 0.42rem 0.55rem; border-radius: 8px; margin-bottom: 0.18rem;
            background: rgba(255,255,255,0.02); border: 1px solid rgba(99,179,237,0.07);
            font-size: 0.76rem; color: #94a3b8;
        }
        .sm-name  { font-weight: 600; color: #e2e8f0; min-width: 112px; }
        .sm-role  { color: #475569; flex: 1; font-size: 0.7rem; }
        .sm-ok    { color: #68d391; font-weight: 600; font-size: 0.72rem; }
        .sm-err   { color: #fc8181; font-weight: 600; font-size: 0.72rem; }
        .sm-time  { color: #334155; font-family: monospace; font-size: 0.68rem; }

        /* ── Scrollbar ── */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(99,179,237,0.22); border-radius: 999px; }
        .stSpinner > div { color: #63b3ed !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# DATA LAYER  –  1,000-row mock sales dataset (cached once per session)
# In production: replace with pd.read_sql("SELECT * FROM sales", engine)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def generate_mock_data() -> pd.DataFrame:
    """Simulate a CRM / database export."""
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
# AGENT BUS  –  the shared state / message bus for the swarm
#
# Each agent reads upstream results and writes its own outputs here.
# Equivalent to a message queue or shared memory in a distributed system.
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class AgentBus:
    # ── Inputs (set by the orchestrator before agents run) ──
    user_prompt: str = ""
    df: Any = None                     # full DataFrame – read-only for agents

    # ── Written by IntentAgent ──
    intent: dict = field(default_factory=dict)

    # ── Written by DataAgent ──
    filtered_df: Any = None
    data_stats: dict = field(default_factory=dict)

    # ── Written by KPIAgent ──
    kpis: dict = field(default_factory=dict)

    # ── Written by VizAgent ──
    charts: list = field(default_factory=list)      # list of (tool_name, plotly_fig)
    tool_names: list = field(default_factory=list)
    tool_summaries: list = field(default_factory=list)

    # ── Written by NarratorAgent ──
    final_text: str = ""

    # ── Written by VerifierAgent ──
    verification: dict = field(default_factory=dict)

    # ── Error flag (any agent can set this) ──
    error: str = ""


# ══════════════════════════════════════════════════════════════════════════════
# BASE AGENT  –  abstract interface all swarm agents must implement
# ══════════════════════════════════════════════════════════════════════════════
class BaseAgent(ABC):
    """
    Abstract base for all swarm agents.
    Subclasses declare name / icon / role and implement run().
    """
    name: str = "BaseAgent"
    icon: str = "🤖"
    role: str = "Generic agent"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._client = None     # lazy-initialised OpenAI client

    def _get_client(self) -> OpenAI:
        """Return a shared OpenRouter-backed OpenAI client."""
        if self._client is None:
            self._client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
                default_headers={
                    "HTTP-Referer": "https://localhost/kpi-agent-swarm",
                    "X-Title": "KPI Agent Swarm",
                },
            )
        return self._client

    @abstractmethod
    def run(self, bus: AgentBus, status_fn=None) -> None:
        """
        Execute this agent's task.
        Reads from bus, writes results back to bus. No return value.
        status_fn(msg: str) is called with live progress updates for the UI.
        """
        ...


# ══════════════════════════════════════════════════════════════════════════════
# AGENT 1: INTENT AGENT  (LLM call 1)
#
# Role: Parse the user's free-form text into structured intent entities.
# Simulates the NLU / entity-extraction layer of Copilot Studio.
# Has a keyword-scan fallback if the LLM fails.
# ══════════════════════════════════════════════════════════════════════════════
class IntentAgent(BaseAgent):
    name = "Intent Agent"
    icon = "🔍"
    role = "Entity & query-type extraction"

    VALID_REGIONS  = {"North", "South", "East", "West", "EMEA"}
    VALID_PRODUCTS = {"Enterprise License", "Cloud Storage", "Consulting", "Support SLA"}
    VALID_STATUSES = {"Won", "Lost", "Pending"}
    VALID_QTYPES   = {"kpi", "trend", "chart", "comparison", "general"}

    _SYSTEM = """\
You are an intent extraction engine for a sales analytics chatbot.
Extract structured entities from the user query. Respond ONLY with valid JSON — no markdown, no explanation.

JSON schema (use null for any field not explicitly mentioned):
{
  "region":        "North" | "South" | "East" | "West" | "EMEA" | "all",
  "product":       "Enterprise License" | "Cloud Storage" | "Consulting" | "Support SLA" | "all",
  "status_filter": "Won" | "Lost" | "Pending" | "all",
  "query_type":    "kpi" | "trend" | "chart" | "comparison" | "general",
  "date_hint":     "last_week" | "last_month" | null
}

query_type guide:
  kpi         → user wants numeric KPI metrics, summary, performance overview
  trend       → user asks about trends, over time, weekly, timeline
  chart       → user explicitly requests a chart type (bar, pie, scatter, donut)
  comparison  → user wants to compare groups / regions / products
  general     → greeting, chit-chat, or unclear request
"""

    def run(self, bus: AgentBus, status_fn=None) -> None:
        if status_fn:
            status_fn(f"{self.icon} **{self.name}** — parsing intent…")

        try:
            client = self._get_client()
            resp   = client.chat.completions.create(
                model="google/gemini-3.1-flash-lite",
                messages=[
                    {"role": "system", "content": self._SYSTEM},
                    {"role": "user",   "content": bus.user_prompt},
                ],
                temperature=0.0,
                max_tokens=160,
            )
            raw = resp.choices[0].message.content.strip()
            # Strip accidental markdown code fences
            if "```" in raw:
                raw = raw.split("```")[1].lstrip("json").strip()
            intent = json.loads(raw)
        except Exception:
            # Graceful keyword-scan fallback
            intent = self._keyword_fallback(bus.user_prompt)

        # Normalise: null / missing → "all"
        for key in ("region", "product", "status_filter"):
            if not intent.get(key):
                intent[key] = "all"
        if intent.get("query_type") not in self.VALID_QTYPES:
            intent["query_type"] = "general"
        intent.setdefault("date_hint", None)

        bus.intent = intent
        if status_fn:
            status_fn(
                f"   ✓ region=**{intent['region']}** · "
                f"product=**{intent['product']}** · "
                f"status=**{intent['status_filter']}** · "
                f"type=**{intent['query_type']}**"
            )

    # ── Fallback: pure keyword matching ────────────────────────────────────
    def _keyword_fallback(self, prompt: str) -> dict:
        p = prompt.lower()

        region = "all"
        for r in sorted(self.VALID_REGIONS, key=len, reverse=True):
            if r.lower() in p:
                region = r
                break

        product = "all"
        for pr in sorted(self.VALID_PRODUCTS, key=len, reverse=True):
            if pr.lower() in p:
                product = pr
                break

        status = "all"
        for s in self.VALID_STATUSES:
            if s.lower() in p:
                status = s
                break

        query_type = "general"
        if any(w in p for w in ["kpi", "metric", "performance", "summary", "overview"]):
            query_type = "kpi"
        elif any(w in p for w in ["trend", "over time", "weekly", "timeline"]):
            query_type = "trend"
        elif any(w in p for w in ["compare", "comparison", " vs ", "versus", "across"]):
            query_type = "comparison"
        elif any(w in p for w in ["chart", "bar", "pie", "scatter", "plot", "graph", "donut"]):
            query_type = "chart"

        return {
            "region": region, "product": product,
            "status_filter": status, "query_type": query_type,
            "date_hint": None,
        }


# ══════════════════════════════════════════════════════════════════════════════
# AGENT 2: DATA AGENT  (pure Python — no LLM)
#
# Role: Apply filters extracted by IntentAgent to the DataFrame.
# Computes data statistics that downstream agents can use.
# Simulates the data-access / retrieval layer.
# ══════════════════════════════════════════════════════════════════════════════
class DataAgent(BaseAgent):
    name = "Data Agent"
    icon = "🗄️"
    role = "DataFrame filter & enrichment"

    def run(self, bus: AgentBus, status_fn=None) -> None:
        if status_fn:
            status_fn(f"{self.icon} **{self.name}** — filtering dataset…")

        intent  = bus.intent
        fdf     = bus.df.copy()
        region  = intent.get("region",        "all")
        product = intent.get("product",       "all")
        status  = intent.get("status_filter", "all")

        if region  and region  != "all": fdf = fdf[fdf["Region"]  == region]
        if product and product != "all": fdf = fdf[fdf["Product"] == product]
        if status  and status  != "all": fdf = fdf[fdf["Status"]  == status]

        bus.filtered_df = fdf

        total = len(fdf)
        bus.data_stats = {
            "total_rows":    total,
            "region_scope":  region,
            "product_scope": product,
            "status_scope":  status,
            "has_data":      total > 0,
            "date_range": (
                f"{fdf['Date'].min()} → {fdf['Date'].max()}" if total > 0 else "n/a"
            ),
        }

        if status_fn:
            status_fn(
                f"   ✓ **{total:,}** rows matched "
                f"({bus.data_stats['date_range']})"
            )


# ══════════════════════════════════════════════════════════════════════════════
# AGENT 3: KPI AGENT  (pure Python — no LLM)
#
# Role: Compute key performance indicators from the filtered dataset.
# Simulates the analytics / calculation layer.
# ══════════════════════════════════════════════════════════════════════════════
class KPIAgent(BaseAgent):
    name = "KPI Agent"
    icon = "📐"
    role = "KPI metric calculation"

    def run(self, bus: AgentBus, status_fn=None) -> None:
        if status_fn:
            status_fn(f"{self.icon} **{self.name}** — computing KPIs…")

        fdf   = bus.filtered_df
        total = len(fdf)

        if total == 0:
            bus.kpis = {}
            if status_fn:
                status_fn("   ⚠️ No data — KPIs skipped")
            return

        won  = fdf[fdf["Status"] == "Won"]
        lost = fdf[fdf["Status"] == "Lost"]
        pend = fdf[fdf["Status"] == "Pending"]

        revenue  = int(won["DealValue"].sum())
        win_rate = round(len(won) / total * 100, 1) if total else 0.0
        avg_deal = int(won["DealValue"].mean()) if len(won) else 0

        bus.kpis = {
            "region":         bus.intent.get("region", "all"),
            "total_deals":    total,
            "total_revenue":  revenue,
            "win_rate":       win_rate,
            "won_deals":      len(won),
            "lost_deals":     len(lost),
            "pending_deals":  len(pend),
            "avg_deal_size":  avg_deal,
        }

        if status_fn:
            status_fn(
                f"   ✓ Revenue: **${revenue:,}** · "
                f"Win rate: **{win_rate}%** · "
                f"Pipeline: **{len(pend)}** pending"
            )


# ══════════════════════════════════════════════════════════════════════════════
# AGENT 4: VIZ AGENT  (LLM call 2)
#
# Role: Decide which chart tool(s) to call based on intent, then execute them.
# Re-uses TOOL_SCHEMAS and execute_tool() from tools.py — zero duplication.
# Simulates the "action / skill" layer of a Copilot Studio agent.
# ══════════════════════════════════════════════════════════════════════════════
class VizAgent(BaseAgent):
    name = "Viz Agent"
    icon = "📊"
    role = "Chart selection & rendering"

    _SYSTEM = """\
You are a data visualisation agent for a sales analytics dashboard.
Given a user query and extracted intent, call the right chart tool(s).

Dataset: 1,000 sales records (last 90 days)
Columns: Date, Region (North/South/East/West/EMEA),
         Product (Enterprise License/Cloud Storage/Consulting/Support SLA),
         DealValue ($5k–$150k), Status (Won/Lost/Pending)

Tool-selection rules:
  query_type=kpi         → call kpi_summary ONLY — do NOT add extra charts
  query_type=trend       → call line_chart
  query_type=comparison  → call bar_chart with group_by set appropriately
  query_type=chart       → pick the best chart type based on the question
  query_type=general     → call kpi_summary + bar_chart (revenue by product)

Always set filter_region and filter_status from the extracted intent.
If region is "all", omit filter_region or set it to "all".
"""

    def run(self, bus: AgentBus, status_fn=None) -> None:
        if status_fn:
            status_fn(f"{self.icon} **{self.name}** — selecting charts…")

        if not bus.data_stats.get("has_data", False):
            bus.charts = []; bus.tool_names = []; bus.tool_summaries = []
            if status_fn:
                status_fn("   ⚠️ No data — chart skipped")
            return

        intent     = bus.intent
        query_type = intent.get("query_type", "general")
        region     = intent.get("region",     "all")
        status_f   = intent.get("status_filter", "all")

        context = (
            f"User query: {bus.user_prompt}\n"
            f"Extracted intent: region={region}, product={intent.get('product','all')}, "
            f"status={status_f}, query_type={query_type}\n"
            f"Rows matched: {bus.data_stats.get('total_rows', 0)}"
        )

        charts: list         = []
        tool_names: list     = []
        tool_summaries: list = []

        try:
            client   = self._get_client()
            messages = [
                {"role": "system", "content": self._SYSTEM},
                {"role": "user",   "content": context},
            ]

            # Agentic function-calling loop (max 4 iterations)
            for _ in range(4):
                resp   = client.chat.completions.create(
                    model="google/gemini-3.1-flash-lite",
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    tool_choice="auto",
                    temperature=0.1,
                )
                choice = resp.choices[0]

                if choice.finish_reason == "tool_calls":
                    assistant_msg = choice.message
                    messages.append(assistant_msg)

                    for tc in assistant_msg.tool_calls:
                        tname = tc.function.name
                        targs = json.loads(tc.function.arguments)
                        tool_names.append(tname)

                        if status_fn:
                            status_fn(f"   🔧 Calling `{tname}`…")

                        fig, summary, extras = execute_tool(tname, targs, bus.df)
                        tool_summaries.append(f"[{tname}] {summary}")

                        if status_fn:
                            status_fn(f"   ✓ {summary}")

                        if fig is not None:
                            charts.append((tname, fig))
                        # If VizAgent calls kpi_summary and KPIAgent found no data
                        if extras is not None and tname == "kpi_summary" and not bus.kpis:
                            bus.kpis = extras

                        messages.append({
                            "role":         "tool",
                            "tool_call_id": tc.id,
                            "content":      summary,
                        })
                else:
                    break   # model is done calling tools

        except Exception as exc:
            bus.error = f"VizAgent: {exc}"
            if status_fn:
                status_fn(f"   ❌ Error: {exc}")

        bus.charts         = charts
        bus.tool_names     = tool_names
        bus.tool_summaries = tool_summaries


# ══════════════════════════════════════════════════════════════════════════════
# AGENT 5: NARRATOR AGENT  (LLM call 3)
#
# Role: Write a concise, data-grounded insight summary.
# Crucially, the actual numbers are INJECTED into the prompt as ground truth —
# so the narrator cannot hallucinate figures. It can only rephrase real data.
# ══════════════════════════════════════════════════════════════════════════════
class NarratorAgent(BaseAgent):
    name = "Narrator Agent"
    icon = "📝"
    role = "Insight summary writing"

    _SYSTEM = """\
You are a senior data analyst writing a brief insight summary for a sales dashboard.
You will receive EXACT computed results. Narrate them clearly and insightfully.

Rules:
1. Write 2–4 sentences only — no bullet points, flowing prose.
2. Always cite specific numbers from the data provided. Do NOT invent figures.
3. Highlight what is notable, surprising, or actionable.
4. Professional but conversational tone.
"""

    def run(self, bus: AgentBus, status_fn=None) -> None:
        if status_fn:
            status_fn(f"{self.icon} **{self.name}** — writing insights…")

        # Build ground-truth context from upstream agents
        sections = []
        if bus.kpis:
            k = bus.kpis
            sections.append(
                "KPI Results:\n"
                f"  • Region: {k.get('region','all')}\n"
                f"  • Total Revenue (Won): ${k.get('total_revenue',0):,}\n"
                f"  • Win Rate: {k.get('win_rate',0)}% "
                f"({k.get('won_deals',0)} won / {k.get('total_deals',0)} total)\n"
                f"  • Lost Deals: {k.get('lost_deals',0)}\n"
                f"  • Pending Pipeline: {k.get('pending_deals',0)} deals\n"
                f"  • Avg Deal Size (Won): ${k.get('avg_deal_size',0):,}"
            )
        if bus.tool_summaries:
            sections.append("Chart Results:\n" + "\n".join(f"  {s}" for s in bus.tool_summaries))

        if not sections:
            bus.final_text = (
                "I couldn't find relevant data for that query. "
                "Try asking about a specific region (North, South, East, West, EMEA) "
                "or a product (Enterprise License, Cloud Storage, Consulting, Support SLA)."
            )
            return

        grounded_data = "\n\n".join(sections)

        try:
            client = self._get_client()
            resp   = client.chat.completions.create(
                model="google/gemini-3.1-flash-lite",
                messages=[
                    {"role": "system", "content": self._SYSTEM},
                    {
                        "role": "user",
                        "content": (
                            f"User asked: {bus.user_prompt}\n\n"
                            f"Data results (use ONLY these numbers):\n{grounded_data}\n\n"
                            f"Write the insight summary:"
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=220,
            )
            bus.final_text = resp.choices[0].message.content.strip()
        except Exception as exc:
            bus.final_text = f"*(Narrator unavailable: {exc})*"

        if status_fn:
            status_fn(f"   ✓ Insights written ({len(bus.final_text)} chars)")


# ══════════════════════════════════════════════════════════════════════════════
# AGENT 6: VERIFIER AGENT  (LLM call 4)
#
# Role: LLM-as-judge — fact-check the Narrator's prose against tool outputs.
# Simulates a quality-gate / guardrail layer in a production AI pipeline.
# ══════════════════════════════════════════════════════════════════════════════
class VerifierAgent(BaseAgent):
    name = "Verifier"
    icon = "✅"
    role = "Fact-checking & accuracy"

    def run(self, bus: AgentBus, status_fn=None) -> None:
        if status_fn:
            status_fn(f"{self.icon} **{self.name}** — fact-checking…")

        if not bus.tool_summaries and not bus.kpis:
            bus.verification = {}
            return

        # Assemble ground truth
        gt_lines = list(bus.tool_summaries)
        if bus.kpis:
            k = bus.kpis
            gt_lines.append(
                f"Revenue=${k.get('total_revenue',0):,}, "
                f"WinRate={k.get('win_rate',0)}%, "
                f"Pending={k.get('pending_deals',0)}, "
                f"Won={k.get('won_deals',0)}, "
                f"Lost={k.get('lost_deals',0)}"
            )
        ground_truth = "\n".join(f"  • {s}" for s in gt_lines)

        try:
            client = self._get_client()
            resp   = client.chat.completions.create(
                model="google/gemini-3.1-flash-lite",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strict fact-checker. Compare the agent's written "
                            "response against the ground-truth tool outputs. "
                            "Check if numbers, percentages, or factual claims contradict "
                            "the data. Minor rounding (±1%) is acceptable.\n"
                            "Respond ONLY with valid JSON — no markdown:\n"
                            '{"verdict": "accurate" | "minor_issues" | "significant_issues", '
                            '"confidence": <integer 0-100>, '
                            '"notes": "<one concise sentence>"}'
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Ground truth:\n{ground_truth}\n\n"
                            f"Agent's response:\n{bus.final_text}"
                        ),
                    },
                ],
                temperature=0.0,
                max_tokens=120,
            )
            raw = resp.choices[0].message.content.strip()
            if "```" in raw:
                raw = raw.split("```")[1].lstrip("json").strip()
            bus.verification = json.loads(raw)
        except Exception:
            bus.verification = {
                "verdict": "unknown", "confidence": 0,
                "notes": "Verification could not complete.",
            }

        if status_fn:
            verdict = bus.verification.get("verdict", "unknown")
            conf    = bus.verification.get("confidence", 0)
            status_fn(f"   ✓ Verdict: **{verdict}** ({conf}% confidence)")


# ══════════════════════════════════════════════════════════════════════════════
# SWARM ORCHESTRATOR  –  coordinates all 6 agents
#
# In production these could run as async tasks or separate microservices.
# Here they run sequentially so you can watch the live status log in the UI.
# ══════════════════════════════════════════════════════════════════════════════
class SwarmOrchestrator:
    """Runs all agents in sequence, tracks timing, returns bus + swarm log."""

    PIPELINE = [
        IntentAgent,
        DataAgent,
        KPIAgent,
        VizAgent,
        NarratorAgent,
        VerifierAgent,
    ]

    def run(
        self,
        user_prompt: str,
        df: pd.DataFrame,
        api_key: str,
        status_fn=None,
    ) -> tuple:
        """
        Execute the full swarm pipeline.

        Returns
        -------
        bus : AgentBus   — all outputs collected by the swarm
        log : list[dict] — per-agent timing/status for the Swarm Monitor UI
        """
        bus: AgentBus = AgentBus(user_prompt=user_prompt, df=df)
        log: list     = []

        total_agents = len(self.PIPELINE)
        for idx, AgentClass in enumerate(self.PIPELINE, 1):
            agent     = AgentClass(api_key=api_key)
            t0        = time.perf_counter()
            error_msg = None

            if status_fn:
                status_fn(
                    f"\n**[{idx}/{total_agents}]** {agent.icon} **{agent.name}** activated"
                )

            try:
                agent.run(bus, status_fn=status_fn)
            except Exception as exc:
                error_msg = str(exc)
                bus.error  = error_msg

            duration = time.perf_counter() - t0
            log.append({
                "agent":    agent.name,
                "icon":     agent.icon,
                "role":     agent.role,
                "status":   f"❌ {error_msg[:35]}…" if error_msg else "✅ Done",
                "ok":       error_msg is None,
                "duration": round(duration, 2),
            })

        return bus, log


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR  –  data preview + API key + 🐝 Swarm Monitor
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # ── Section 1: Data Layer ──────────────────────────────────────────────
    st.markdown(
        "<h2 style='color:#63b3ed; font-size:1.05rem; margin-bottom:0.2rem;'>"
        "⚙️ Backend Data Layer</h2>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Raw dataset the swarm reads from. "
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
    st.markdown("**Schema**")
    for col, dtype in df.dtypes.items():
        st.markdown(f"- `{col}` — *{dtype}*")
    st.divider()

    # ── Section 2: API Key ─────────────────────────────────────────────────
    st.markdown(
        "<span style='font-size:0.72rem; font-weight:600; color:#a78bfa; "
        "text-transform:uppercase; letter-spacing:0.06em;'>🔑 OpenRouter API Key</span>",
        unsafe_allow_html=True,
    )
    sidebar_key = st.text_input(
        "API Key", value="", type="password",
        placeholder="sk-or-v1-…  (overrides .env)",
        label_visibility="collapsed",
    )
    st.caption("Leave blank to use the key from `.env` or the environment.")
    st.divider()

    # ── Section 3: 🐝 Swarm Monitor ───────────────────────────────────────
    st.markdown(
        "<h2 style='color:#68d391; font-size:1.05rem; margin-bottom:0.2rem;'>"
        "🐝 Swarm Monitor</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Live status of the last agent swarm run.")

    # Render swarm log if it exists in session state
    if "swarm_log" in st.session_state and st.session_state.swarm_log:
        rows_html = ""
        for entry in st.session_state.swarm_log:
            status_cls  = "sm-ok" if entry["ok"] else "sm-err"
            status_text = entry["status"]
            rows_html += (
                f"<div class='sm-row'>"
                f"<span>{entry['icon']}</span>"
                f"<span class='sm-name'>{entry['agent']}</span>"
                f"<span class='sm-role'>{entry['role']}</span>"
                f"<span class='{status_cls}'>{status_text}</span>"
                f"<span class='sm-time'>{entry['duration']}s</span>"
                f"</div>"
            )
        st.markdown(rows_html, unsafe_allow_html=True)
    else:
        st.caption("*(No runs yet — send a message to activate the swarm.)*")

    st.divider()
    st.caption("🔒 Data is generated locally. Charts powered by Plotly + Gemini.")


# ══════════════════════════════════════════════════════════════════════════════
# API KEY RESOLUTION
# Priority: Streamlit secrets → .env / env var → sidebar input
# ══════════════════════════════════════════════════════════════════════════════
def _get_api_key() -> str:
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    env_key = os.getenv("OPENROUTER_API_KEY", "")
    if env_key:
        return env_key
    return sidebar_key.strip()


OPENROUTER_API_KEY = _get_api_key()


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE  –  dual-track history
#
# api_messages    : text-only history sent to LLMs (no Plotly figs)
# display_history : full display items including charts, KPI cards, etc.
# swarm_log       : per-agent timing from the most recent swarm run
# ══════════════════════════════════════════════════════════════════════════════
_WELCOME = (
    "👋 Hello! I'm your **Sales KPI Agent Swarm**.\n\n"
    "When you send a message, **6 specialised AI agents** activate in sequence:\n"
    "1. 🔍 **Intent Agent** — extracts what you're asking for\n"
    "2. 🗄️ **Data Agent** — filters the 1,000-row dataset\n"
    "3. 📐 **KPI Agent** — computes metrics (revenue, win rate, pipeline)\n"
    "4. 📊 **Viz Agent** — selects and renders the right charts\n"
    "5. 📝 **Narrator Agent** — writes a grounded insight summary\n"
    "6. ✅ **Verifier** — fact-checks the narrative vs. real data\n\n"
    "Watch the **🐝 Swarm Monitor** in the sidebar for live agent status.\n\n"
    "**Try asking:**\n"
    "- *\"Show me KPIs for the West region\"* → metric cards\n"
    "- *\"Revenue trend for EMEA by product\"* → 📈 line chart\n"
    "- *\"Compare revenue across all regions\"* → 📊 bar chart\n"
    "- *\"Pie chart of deal status for North\"* → 🥧 donut chart\n\n"
    "**Regions:** North · South · East · West · EMEA  \n"
    "**Products:** Enterprise License · Cloud Storage · Consulting · Support SLA"
)

if "api_messages"    not in st.session_state:
    st.session_state.api_messages = []
if "display_history" not in st.session_state:
    st.session_state.display_history = [
        {"role": "assistant", "elements": [{"type": "text", "data": _WELCOME}]}
    ]
if "swarm_log" not in st.session_state:
    st.session_state.swarm_log = []


# ══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h1>🐝 Sales KPI Agent Swarm</h1>"
    "<p style='color:#475569; margin-top:-0.5rem; margin-bottom:1.5rem; font-size:0.9rem;'>"
    "6-agent pipeline · Gemini Flash · OpenRouter · Plotly · Streamlit"
    "</p>",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# RENDER HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def render_kpi_cards(metrics: dict) -> None:
    """Render four metric cards from a kpi_summary result."""
    region_label = (
        "All Regions" if metrics.get("region") == "all"
        else f"{metrics.get('region', '?')} Region"
    )
    st.markdown(
        f"<span class='agent-badge'>📐 KPI Summary — {region_label}</span>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            "💰 Revenue (Won)",
            f"${metrics.get('total_revenue', 0):,}",
            f"avg ${metrics.get('avg_deal_size', 0):,} / deal",
        )
    with c2:
        st.metric(
            "🏆 Win Rate",
            f"{metrics.get('win_rate', 0)}%",
            f"{metrics.get('won_deals',0)} won · {metrics.get('lost_deals',0)} lost",
        )
    with c3:
        st.metric(
            "⏳ Pipeline",
            f"{metrics.get('pending_deals', 0)} deals",
            f"Total: {metrics.get('total_deals', 0)}",
        )
    with c4:
        st.metric(
            "📋 Total Deals",
            f"{metrics.get('total_deals', 0)}",
            f"Won {metrics.get('won_deals',0)} / Lost {metrics.get('lost_deals',0)}",
        )


def render_verification_badge(v: dict) -> None:
    """Render the verifier result as a styled inline badge."""
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
            max-width:640px;
        '>
            <span style='font-size:1rem;flex-shrink:0'>{icon}</span>
            <div>
                <span style='font-weight:700; color:{colour};'>{label}</span>
                <span style='color:rgba(255,255,255,0.3); margin-left:0.5rem;'>
                    ({confidence}% confidence)
                </span><br>
                <span style='color:rgba(255,255,255,0.5);'>{notes}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_intent_card(intent: dict) -> None:
    """Render the extracted intent as a compact card inside an expander."""
    with st.expander("🔍 Extracted Intent (IntentAgent output)", expanded=False):
        st.markdown(
            f"""<div class='intent-card'>
                <span class='intent-lbl'>Region</span>&nbsp; {intent.get('region', 'all')}
                &nbsp;&nbsp;·&nbsp;&nbsp;
                <span class='intent-lbl'>Product</span>&nbsp; {intent.get('product', 'all')}
                &nbsp;&nbsp;·&nbsp;&nbsp;
                <span class='intent-lbl'>Status</span>&nbsp; {intent.get('status_filter', 'all')}
                &nbsp;&nbsp;·&nbsp;&nbsp;
                <span class='intent-lbl'>Query type</span>&nbsp; {intent.get('query_type', 'general')}
                &nbsp;&nbsp;·&nbsp;&nbsp;
                <span class='intent-lbl'>Date hint</span>&nbsp; {intent.get('date_hint') or 'none'}
            </div>""",
            unsafe_allow_html=True,
        )


def render_display_item(item: dict) -> None:
    """Render a single display-history entry inside st.chat_message."""
    for el in item.get("elements", []):
        etype = el.get("type")
        data  = el.get("data")

        if etype == "text":
            st.markdown(data)

        elif etype == "chart":
            st.plotly_chart(
                data,
                use_container_width=True,
                config={"displayModeBar": True, "displaylogo": False},
            )

        elif etype == "kpi":
            render_kpi_cards(data)

        elif etype == "tool_badges":
            badges = "".join(
                f"<span class='tool-badge'>🔧 {t}</span>" for t in data
            )
            st.markdown(badges, unsafe_allow_html=True)

        elif etype == "swarm_badge":
            # data = {"agents": int, "duration": float}
            st.markdown(
                f"<span class='swarm-badge'>"
                f"🐝 Swarm · {data.get('agents', 0)} agents · "
                f"{data.get('duration', 0):.1f}s total"
                f"</span>",
                unsafe_allow_html=True,
            )

        elif etype == "intent":
            render_intent_card(data)

        elif etype == "verification":
            render_verification_badge(data)


# ══════════════════════════════════════════════════════════════════════════════
# RENDER CHAT HISTORY
# ══════════════════════════════════════════════════════════════════════════════
for item in st.session_state.display_history:
    with st.chat_message(item["role"]):
        render_display_item(item)


# ══════════════════════════════════════════════════════════════════════════════
# CHAT INPUT  +  SWARM INVOCATION
# ══════════════════════════════════════════════════════════════════════════════
user_prompt = st.chat_input(
    "Ask the swarm anything…  e.g. 'KPIs for West' · 'Trend for EMEA' · 'Compare all regions'"
)

if user_prompt:
    # ── Guard: API key required ──────────────────────────────────────────────
    if not OPENROUTER_API_KEY:
        st.error(
            "⚠️ No API key found. Add your OpenRouter key to `.env` as "
            "`OPENROUTER_API_KEY` or paste it in the sidebar."
        )
        st.stop()

    # ── 1. Show user message ─────────────────────────────────────────────────
    st.session_state.display_history.append(
        {"role": "user", "elements": [{"type": "text", "data": user_prompt}]}
    )
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # ── 2. Run the swarm with a live status log ──────────────────────────────
    orchestrator = SwarmOrchestrator()
    swarm_error  = False
    t_swarm_start = time.perf_counter()

    with st.chat_message("assistant"):
        with st.status("🐝 Swarm activating…", expanded=True) as status_box:
            try:
                bus, swarm_log = orchestrator.run(
                    user_prompt    = user_prompt,
                    df             = df,
                    api_key        = OPENROUTER_API_KEY,
                    status_fn      = status_box.write,
                )
            except Exception as exc:
                bus            = AgentBus(user_prompt=user_prompt, df=df)
                bus.error      = str(exc)
                bus.final_text = f"⚠️ Swarm error: `{exc}`"
                swarm_log      = []
                swarm_error    = True

            # Collapse status box with a summary label
            swarm_duration = time.perf_counter() - t_swarm_start
            if swarm_error or bus.error:
                status_box.update(
                    label=f"❌ Swarm error after {swarm_duration:.1f}s",
                    state="error", expanded=True,
                )
            elif bus.verification.get("verdict") == "significant_issues":
                status_box.update(
                    label=f"⚠️ Done ({swarm_duration:.1f}s) — accuracy issues flagged",
                    state="complete", expanded=False,
                )
            else:
                status_box.update(
                    label=f"✅ Swarm complete · {swarm_duration:.1f}s · {len(SwarmOrchestrator.PIPELINE)} agents",
                    state="complete", expanded=False,
                )

        # ── 3. Assemble and render display elements ──────────────────────────
        display_elements: list = []

        # ─ a) Swarm summary badge ─
        swarm_badge_data = {
            "agents":   len(SwarmOrchestrator.PIPELINE),
            "duration": swarm_duration,
        }
        st.markdown(
            f"<span class='swarm-badge'>"
            f"🐝 Swarm · {swarm_badge_data['agents']} agents · "
            f"{swarm_badge_data['duration']:.1f}s total"
            f"</span>",
            unsafe_allow_html=True,
        )
        display_elements.append({"type": "swarm_badge", "data": swarm_badge_data})

        # ─ b) Tool badges ─
        if bus.tool_names:
            badges = "".join(
                f"<span class='tool-badge'>🔧 {t}</span>" for t in bus.tool_names
            )
            st.markdown(badges, unsafe_allow_html=True)
            display_elements.append({"type": "tool_badges", "data": bus.tool_names})

        # ─ c) Intent card (expandable) ─
        if bus.intent:
            render_intent_card(bus.intent)
            display_elements.append({"type": "intent", "data": bus.intent})

        # ─ d) KPI metric cards ─
        if bus.kpis:
            render_kpi_cards(bus.kpis)
            display_elements.append({"type": "kpi", "data": bus.kpis})

        # ─ e) Charts ─
        for _tname, fig in bus.charts:
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": True, "displaylogo": False},
            )
            display_elements.append({"type": "chart", "data": fig})

        # ─ f) Narrator's insight text ─
        if bus.final_text:
            st.markdown(bus.final_text)
            display_elements.append({"type": "text", "data": bus.final_text})

        # ─ g) Verification badge ─
        if bus.verification:
            render_verification_badge(bus.verification)
            display_elements.append({"type": "verification", "data": bus.verification})

    # ── 4. Persist to session state ──────────────────────────────────────────
    st.session_state.display_history.append(
        {"role": "assistant", "elements": display_elements}
    )
    # Update swarm log (sidebar Swarm Monitor)
    st.session_state.swarm_log = swarm_log

    # Update rolling LLM-facing history (text only — no Plotly figs)
    st.session_state.api_messages.append({"role": "user",      "content": user_prompt})
    st.session_state.api_messages.append({"role": "assistant", "content": bus.final_text or ""})

    # Keep history bounded to last 20 turns (40 messages)
    if len(st.session_state.api_messages) > 40:
        st.session_state.api_messages = st.session_state.api_messages[-40:]
