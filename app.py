"""
╔══════════════════════════════════════════════════════════════════════════╗
║              OSS SALES KPI AGENT  –  app.py                            ║
║  A local, open-source alternative to Microsoft Copilot Studio           ║
║                                                                          ║
║  Architecture at a glance:                                              ║
║   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐  ║
║   │  DATA LAYER      │ → │  LOGIC ENGINE    │ → │  UI / RENDERER   │  ║
║   │  (mock database) │   │  (mock LLM)      │   │  (Streamlit)     │  ║
║   └──────────────────┘   └──────────────────┘   └──────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# ── Standard library ──────────────────────────────────────────────────────────
import random
from datetime import datetime, timedelta

# ── Third-party ───────────────────────────────────────────────────────────────
import pandas as pd
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 │ INITIALIZATION & DATA LAYER
# This section replaces a real database or Excel file. In a production system
# you would swap generate_mock_data() with a SQL query or an API call.
# ══════════════════════════════════════════════════════════════════════════════

# ── Page config must be the FIRST Streamlit call ─────────────────────────────
st.set_page_config(
    page_title="Dynamic KPI Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject custom CSS for a premium dark-mode look ───────────────────────────
st.markdown(
    """
    <style>
        /* ── Google Font ── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* ── Global reset ── */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* ── App background ── */
        .stApp {
            background: linear-gradient(135deg, #0d0f1a 0%, #111827 50%, #0d1520 100%);
            min-height: 100vh;
        }

        /* ── Main content area ── */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #111827 0%, #0d1520 100%);
            border-right: 1px solid rgba(99, 179, 237, 0.15);
        }
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] caption,
        [data-testid="stSidebar"] p {
            color: #94a3b8 !important;
        }

        /* ── Chat messages ── */
        [data-testid="stChatMessage"] {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(99,179,237,0.12);
            border-radius: 16px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.75rem;
            backdrop-filter: blur(8px);
        }

        /* ── Metric cards ── */
        [data-testid="stMetric"] {
            background: rgba(99,179,237,0.06);
            border: 1px solid rgba(99,179,237,0.2);
            border-radius: 14px;
            padding: 1.2rem 1rem;
            text-align: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(99,179,237,0.18);
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #63b3ed !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 700 !important;
            color: #f1f5f9 !important;
        }
        [data-testid="stMetricDelta"] {
            font-size: 0.8rem !important;
        }

        /* ── Chat input ── */
        [data-testid="stChatInput"] {
            border: 1.5px solid rgba(99,179,237,0.35) !important;
            border-radius: 14px !important;
            background: rgba(255,255,255,0.04) !important;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: #63b3ed !important;
            box-shadow: 0 0 0 3px rgba(99,179,237,0.15) !important;
        }

        /* ── Page title ── */
        h1 {
            background: linear-gradient(90deg, #63b3ed, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.4rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }

        /* ── Divider ── */
        hr {
            border-color: rgba(99,179,237,0.15) !important;
        }

        /* ── Bar chart ── */
        [data-testid="stVegaLiteChart"] {
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(99,179,237,0.15);
        }

        /* ── Sidebar dataframe ── */
        [data-testid="stDataFrame"] {
            border: 1px solid rgba(99,179,237,0.15);
            border-radius: 10px;
            overflow: hidden;
        }

        /* ── Badges / info boxes ── */
        .kpi-badge {
            display: inline-block;
            background: rgba(99,179,237,0.12);
            border: 1px solid rgba(99,179,237,0.3);
            border-radius: 999px;
            padding: 0.2rem 0.85rem;
            font-size: 0.75rem;
            font-weight: 600;
            color: #63b3ed;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        /* ── Scrollbar ── */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb {
            background: rgba(99,179,237,0.25);
            border-radius: 999px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── [DATA LAYER] Generate 1,000 rows of mock sales data ──────────────────────
# @st.cache_data ensures this function only runs ONCE per session – just like
# reading from a real database or loading a CSV file once and caching the result.
@st.cache_data
def generate_mock_data() -> pd.DataFrame:
    """
    Simulates a CRM or sales database export.
    In a real system this would be:
        pd.read_sql("SELECT * FROM sales", engine)
        OR
        pd.read_csv("sales_data.csv")
    """
    random.seed(42)  # fixed seed → reproducible mock data

    NUM_ROWS   = 1_000
    REGIONS    = ["North", "South", "East", "West", "EMEA"]
    PRODUCTS   = [
        "Enterprise License",
        "Cloud Storage",
        "Consulting",
        "Support SLA",
    ]
    STATUSES   = ["Won", "Lost", "Pending"]
    # Weights make the data a bit more realistic (more Pending & Lost than Won)
    STATUS_WTS = [0.35, 0.40, 0.25]

    today = datetime.now()
    rows = []
    for _ in range(NUM_ROWS):
        days_ago = random.randint(0, 89)          # last 90 days
        rows.append({
            "Date":      today - timedelta(days=days_ago),
            "Region":    random.choice(REGIONS),
            "Product":   random.choice(PRODUCTS),
            "DealValue": random.randint(5_000, 150_000),
            "Status":    random.choices(STATUSES, weights=STATUS_WTS, k=1)[0],
        })

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date  # keep date only
    return df


# Load the dataset once
df = generate_mock_data()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 │ UI STRUCTURE – SIDEBAR (Backend Data Layer panel)
# This sidebar is the "transparency window" – it shows the raw data that the
# agent is working with. Equivalent to opening the source Excel/database.
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        "<h2 style='color:#63b3ed; font-size:1.1rem; margin-bottom:0.25rem;'>"
        "⚙️ Backend Data Layer"
        "</h2>",
        unsafe_allow_html=True,
    )
    st.caption(
        "This panel represents the **raw data source** "
        "(a database table, CRM export, or Excel file) "
        "that the KPI Agent reads from. In production, "
        "this is replaced by a live SQL or API connection."
    )
    st.divider()

    # Display a preview of the raw data
    st.markdown(
        "<span class='kpi-badge'>📄 Data Preview – first 15 rows</span>",
        unsafe_allow_html=True,
    )
    st.dataframe(
        df.head(15),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # Row count
    st.markdown(
        f"**Total records in dataset:** `{len(df):,}` rows",
    )

    # Quick schema info
    st.markdown("**Columns**")
    for col, dtype in df.dtypes.items():
        st.markdown(
            f"- `{col}` — *{dtype}*",
        )

    st.divider()
    st.caption("🔒 Data is generated locally. No external APIs are used.")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 │ CHAT INTERFACE & SESSION STATE
# st.session_state is Streamlit's way of persisting data across reruns.
# Each message is stored as {"role": "user"|"assistant", "content": "..."}.
# ══════════════════════════════════════════════════════════════════════════════

# ── Page header ──────────────────────────────────────────────────────────────
st.markdown(
    "<h1>💬 Autonomous KPI Agent</h1>"
    "<p style='color:#64748b; margin-top:-0.5rem; margin-bottom:1.5rem; font-size:0.95rem;'>"
    "An open-source, local alternative to Microsoft Copilot Studio · "
    "Powered by Pandas + Streamlit"
    "</p>",
    unsafe_allow_html=True,
)

# ── Initialise chat history (runs only on first load) ────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hello! I'm your **Autonomous Sales KPI Agent**.\n\n"
                "I have access to **1,000 sales records** spanning the last 90 days "
                "across five regions.\n\n"
                "Try asking me something like:\n"
                "- *\"Show me the KPIs for the West region\"*\n"
                "- *\"What is the performance of EMEA?\"*\n"
                "- *\"Give me a breakdown for North\"*\n\n"
                "Available regions: **North · South · East · West · EMEA**"
            ),
        }
    ]

# ── Render existing messages ──────────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ── Chat input box ────────────────────────────────────────────────────────────
user_prompt = st.chat_input("Ask for regional KPIs…  e.g. 'Show me KPIs for West'")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 │ LOGIC ENGINE – INTENT / ENTITY EXTRACTION  (simulates an LLM)
#
# In a real Copilot Studio agent this step would call OpenAI / Gemini / Azure
# to extract the entity (the region name) from free-form text.
#
# Here we simulate that with a simple keyword scan – the important point is
# that the *interface contract* is identical: we receive a string and return a
# structured value (target_region) for the downstream KPI calculator.
# ══════════════════════════════════════════════════════════════════════════════

VALID_REGIONS = ["North", "South", "East", "West", "EMEA"]

if user_prompt:
    # ── 1. Persist & display the user message ────────────────────────────────
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # ── 2. [MOCK LLM] Entity extraction ──────────────────────────────────────
    # Convert to lowercase for case-insensitive matching.
    # A real LLM call would look like:
    #     response = openai.chat.completions.create(...)
    #     target_region = parse_region_from_response(response)
    prompt_lower  = user_prompt.lower()
    target_region = None

    for region in VALID_REGIONS:
        if region.lower() in prompt_lower:
            target_region = region   # first match wins
            break

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 5 │ KPI CALCULATION & RENDERING  (the "Adaptive Card")
    #
    # This is where the agent's "action" runs:
    #   Filter → Calculate → Visualise
    # ══════════════════════════════════════════════════════════════════════════

    if target_region:
        with st.chat_message("assistant"):

            # ── Header ───────────────────────────────────────────────────────
            st.markdown(
                f"### 📊 KPI Dashboard — **{target_region} Region**\n"
                f"<span class='kpi-badge'>🤖 Agent action: filter → calculate → render</span>",
                unsafe_allow_html=True,
            )
            st.markdown("")  # spacer

            # ── [FILTER] Keep only rows for the requested region ─────────────
            filtered_df = df[df["Region"] == target_region].copy()

            total_deals = len(filtered_df)

            if total_deals == 0:
                st.warning(
                    f"No data found for the **{target_region}** region."
                )
            else:
                # ── [CALCULATE] Derive KPIs ───────────────────────────────────
                won_df   = filtered_df[filtered_df["Status"] == "Won"]
                lost_df  = filtered_df[filtered_df["Status"] == "Lost"]
                pend_df  = filtered_df[filtered_df["Status"] == "Pending"]

                # KPI 1 – Total Revenue (won deals only)
                total_revenue   = int(won_df["DealValue"].sum())

                # KPI 2 – Win Rate
                win_rate        = (len(won_df) / total_deals) * 100

                # KPI 3 – Active Pipeline (deals still pending)
                active_pipeline = len(pend_df)

                # Extra context figures for deltas
                avg_deal_size   = (
                    int(won_df["DealValue"].mean()) if len(won_df) > 0 else 0
                )
                lost_count      = len(lost_df)

                # ── [VISUALISE] Metric cards ──────────────────────────────────
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        label="💰 Total Revenue (Won)",
                        value=f"${total_revenue:,.0f}",
                        delta=f"Avg deal: ${avg_deal_size:,.0f}",
                    )

                with col2:
                    st.metric(
                        label="🏆 Win Rate",
                        value=f"{win_rate:.1f}%",
                        delta=f"{len(won_df)} won · {lost_count} lost",
                    )

                with col3:
                    st.metric(
                        label="⏳ Active Pipeline",
                        value=f"{active_pipeline} deals",
                        delta=f"Total reviewed: {total_deals}",
                    )

                st.markdown("---")

                # ── [CHART] Revenue by Product (Won deals only) ───────────────
                if len(won_df) > 0:
                    st.markdown(
                        "**📦 Revenue by Product** *(Won deals only)*"
                    )

                    product_revenue = (
                        won_df.groupby("Product")["DealValue"]
                        .sum()
                        .reset_index()
                        .rename(columns={"DealValue": "Revenue ($)"})
                        .sort_values("Revenue ($)", ascending=False)
                    )

                    st.bar_chart(
                        product_revenue.set_index("Product"),
                        use_container_width=True,
                        height=280,
                        color="#63b3ed",
                    )
                else:
                    st.info("No won deals to chart yet.")

                # ── [CHART] Deal Status breakdown (pie-like via bar) ──────────
                st.markdown("")
                st.markdown("**📋 Deal Status Breakdown**")
                status_counts = (
                    filtered_df["Status"]
                    .value_counts()
                    .reset_index()
                    .rename(columns={"count": "Count"})
                )
                st.bar_chart(
                    status_counts.set_index("Status"),
                    use_container_width=True,
                    height=200,
                    color="#a78bfa",
                )

            # ── Persist a text summary in session state ───────────────────────
            # This is important: the chat history must be serialisable (no DataFrames).
            # We store a plain-text summary so the conversation context is preserved.
            summary_text = (
                f"📊 **{target_region} Region KPI Summary**\n"
                f"- 💰 Total Revenue: **${total_revenue:,.0f}**\n"
                f"- 🏆 Win Rate: **{win_rate:.1f}%** "
                f"({len(won_df)} won / {total_deals} total)\n"
                f"- ⏳ Active Pipeline: **{active_pipeline} pending deals**\n"
                f"- 📦 Revenue breakdown chart rendered above."
            )
            st.session_state.messages.append(
                {"role": "assistant", "content": summary_text}
            )

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 6 │ ERROR HANDLING – No region detected
    # ══════════════════════════════════════════════════════════════════════════

    else:
        # The "LLM" could not extract a valid region entity → graceful fallback
        fallback_message = (
            "🤔 I wasn't able to identify a **sales region** in your message.\n\n"
            "I currently support the following regions:\n"
            "**North · South · East · West · EMEA**\n\n"
            "Could you try phrasing your request like:\n"
            "- *\"Show me KPIs for EMEA\"*\n"
            "- *\"What's the performance of the South region?\"*\n"
            "- *\"Give me a West breakdown\"*"
        )

        with st.chat_message("assistant"):
            st.markdown(fallback_message)

        st.session_state.messages.append(
            {"role": "assistant", "content": fallback_message}
        )
