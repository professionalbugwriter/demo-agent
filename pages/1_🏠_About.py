import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="KPI Agent Swarm · About",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    footer { visibility: hidden; }
    [data-testid="collapsedControl"] { display: none; }
</style>
""", unsafe_allow_html=True)

PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #000;
    color: #fff;
    font-family: 'Inter', sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  a { color: inherit; text-decoration: none; }

  .page {
    max-width: 780px;
    margin: 0 auto;
    padding: 4rem 2rem 5rem;
  }

  /* ── Brand block ── */
  .brand {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding-bottom: 2.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 2.5rem;
  }
  .logo-s {
    width: 40px; height: 40px;
    background: #fff;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; font-weight: 900; color: #000;
    flex-shrink: 0;
  }
  .brand-name {
    font-size: 1rem; font-weight: 700;
    letter-spacing: 0.06em; text-transform: uppercase;
    color: #fff; line-height: 1;
  }
  .brand-url {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.35);
    margin-top: 0.2rem;
    letter-spacing: 0.02em;
  }
  .brand-url a:hover { color: rgba(255,255,255,0.7); }

  /* ── Typography ── */
  h1 {
    font-size: 1.95rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    line-height: 1.2;
    color: #fff;
    margin-bottom: 1rem;
  }
  h1 span {
    background: linear-gradient(90deg, #facc15, #fb923c, #f43f5e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  p {
    font-size: 0.97rem;
    color: rgba(255,255,255,0.5);
    line-height: 1.85;
    margin-bottom: 1.5rem;
  }
  p strong { color: rgba(255,255,255,0.8); font-weight: 600; }

  h2 {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.25);
    margin: 2.5rem 0 1rem;
  }

  /* ── Agent pipeline ── */
  .pipeline {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    margin-bottom: 1.8rem;
  }
  .agent-row {
    display: flex;
    align-items: flex-start;
    gap: 0.9rem;
    padding: 0.9rem 1.1rem;
    border-radius: 12px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    transition: border-color 0.2s;
  }
  .agent-row:hover { border-color: rgba(255,255,255,0.14); }
  .agent-icon {
    font-size: 1.1rem;
    flex-shrink: 0;
    margin-top: 0.05rem;
  }
  .agent-body {}
  .agent-name {
    font-size: 0.84rem;
    font-weight: 700;
    color: rgba(255,255,255,0.85);
    margin-bottom: 0.18rem;
  }
  .agent-name .badge {
    display: inline-block;
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 0.1rem 0.5rem;
    border-radius: 999px;
    margin-left: 0.45rem;
    vertical-align: middle;
  }
  .badge-llm  { background: rgba(168,85,247,0.15); color: #a855f7; border: 1px solid rgba(168,85,247,0.25); }
  .badge-py   { background: rgba(34,211,238,0.12); color: #22d3ee; border: 1px solid rgba(34,211,238,0.2); }
  .agent-desc {
    font-size: 0.8rem;
    color: rgba(255,255,255,0.35);
    line-height: 1.55;
  }

  /* ── Chart type pills ── */
  .pills {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }
  .pill {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.35rem 0.85rem;
    border-radius: 999px;
    font-size: 0.8rem; font-weight: 500;
    border: 1px solid;
  }
  .p1 { color: #fb923c; border-color: rgba(251,146,60,0.3); background: rgba(251,146,60,0.07); }
  .p2 { color: #facc15; border-color: rgba(250,204,21,0.3); background: rgba(250,204,21,0.07); }
  .p3 { color: #a855f7; border-color: rgba(168,85,247,0.3); background: rgba(168,85,247,0.07); }
  .p4 { color: #22d3ee; border-color: rgba(34,211,238,0.3); background: rgba(34,211,238,0.07); }
  .p5 { color: #34d399; border-color: rgba(52,211,153,0.3); background: rgba(52,211,153,0.07); }

  /* ── Dataset columns ── */
  .cols {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }
  .col-item {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 0.75rem 1rem;
  }
  .col-name {
    font-size: 0.78rem; font-weight: 600;
    font-family: 'Courier New', monospace;
    color: rgba(255,255,255,0.7);
    margin-bottom: 0.2rem;
  }
  .col-type { font-size: 0.7rem; color: rgba(255,255,255,0.25); }

  /* ── Tech stack ── */
  .stack {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }
  .tech {
    font-size: 0.78rem; font-weight: 500;
    padding: 0.3rem 0.8rem;
    border-radius: 8px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.09);
    color: rgba(255,255,255,0.55);
  }

  /* ── CTA ── */
  .cta {
    margin-top: 2.5rem;
    padding-top: 2rem;
    border-top: 1px solid rgba(255,255,255,0.07);
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  .btn {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.7rem 1.5rem;
    border-radius: 999px;
    font-size: 0.85rem; font-weight: 600;
    transition: opacity 0.2s;
  }
  .btn:hover { opacity: 0.8; }
  .btn-solid { background: #fff; color: #000; }
  .btn-outline {
    background: transparent; color: rgba(255,255,255,0.6);
    border: 1px solid rgba(255,255,255,0.15);
  }
</style>
</head>
<body>
<div class="page">

  <!-- Brand -->
  <div class="brand">
    <div class="logo-s">S</div>
    <div class="brand-info">
      <div class="brand-name">CraftSync</div>
      <div class="brand-url"><a href="https://www.thecraftsync.com" target="_blank">thecraftsync.com ↗</a></div>
    </div>
  </div>

  <!-- Intro -->
  <h1>Sales KPI <span>Agent Swarm</span></h1>

  <p>
    Built by <strong>CraftSync</strong> — strategic design meeting technical precision.
    An open-source, local alternative to Microsoft Copilot Studio that orchestrates
    <strong>six specialised AI agents</strong> in real-time to answer natural language
    questions about sales data with interactive charts and verified insights.
  </p>

  <p>
    Every message activates a coordinated pipeline: one agent parses your intent,
    another filters the dataset, a third computes KPIs, a fourth renders charts,
    a fifth narrates the findings — and a sixth fact-checks every claim against the
    actual data before you see it.
  </p>

  <!-- Agent pipeline -->
  <h2>Agent Pipeline</h2>
  <div class="pipeline">

    <div class="agent-row">
      <div class="agent-icon">🔍</div>
      <div class="agent-body">
        <div class="agent-name">
          Intent Agent
          <span class="badge badge-llm">LLM</span>
        </div>
        <div class="agent-desc">
          Extracts structured entities — region, product, status filter, and query
          type — from free-form natural language using Gemini 3.1 Flash Lite.
          Falls back to keyword scanning if the LLM is unavailable.
        </div>
      </div>
    </div>

    <div class="agent-row">
      <div class="agent-icon">🗄️</div>
      <div class="agent-body">
        <div class="agent-name">
          Data Agent
          <span class="badge badge-py">Python</span>
        </div>
        <div class="agent-desc">
          Applies the parsed filters to the sales DataFrame using Pandas.
          Computes data statistics (row count, date range) for downstream agents.
        </div>
      </div>
    </div>

    <div class="agent-row">
      <div class="agent-icon">📐</div>
      <div class="agent-body">
        <div class="agent-name">
          KPI Agent
          <span class="badge badge-py">Python</span>
        </div>
        <div class="agent-desc">
          Computes key metrics — total revenue (won deals), win rate, average deal
          size, pipeline count — from the filtered dataset with no LLM involvement.
        </div>
      </div>
    </div>

    <div class="agent-row">
      <div class="agent-icon">📊</div>
      <div class="agent-body">
        <div class="agent-name">
          Viz Agent
          <span class="badge badge-llm">LLM + Tools</span>
        </div>
        <div class="agent-desc">
          Uses Gemini function-calling to select and execute the right chart tool
          (bar, line, pie, scatter, KPI summary) based on query type. Routes
          automatically — no manual chart selection required.
        </div>
      </div>
    </div>

    <div class="agent-row">
      <div class="agent-icon">📝</div>
      <div class="agent-body">
        <div class="agent-name">
          Narrator Agent
          <span class="badge badge-llm">LLM</span>
        </div>
        <div class="agent-desc">
          Writes a 2–4 sentence analytical summary with the actual computed numbers
          injected as ground truth. The model can only narrate real data —
          hallucination is structurally prevented.
        </div>
      </div>
    </div>

    <div class="agent-row">
      <div class="agent-icon">✅</div>
      <div class="agent-body">
        <div class="agent-name">
          Verifier
          <span class="badge badge-llm">LLM-as-Judge</span>
        </div>
        <div class="agent-desc">
          A final quality gate that compares the Narrator's prose against the
          tool output data. Returns a verdict (accurate / minor issues /
          significant issues) with a confidence score before the response is shown.
        </div>
      </div>
    </div>

  </div>

  <!-- Chart types -->
  <h2>Chart types</h2>
  <div class="pills">
    <span class="pill p1">📊 Bar Chart</span>
    <span class="pill p2">📈 Line Chart</span>
    <span class="pill p3">🥧 Pie / Donut</span>
    <span class="pill p4">🔵 Scatter Plot</span>
    <span class="pill p5">🎯 KPI Summary</span>
  </div>
  <p>
    The Viz Agent picks the right chart automatically based on your question.
    Bar charts for comparisons, line charts for trends, pie charts for proportions,
    scatter plots for distribution analysis, and KPI cards when you need
    headline numbers. It can call multiple tools in a single response.
  </p>

  <!-- Dataset -->
  <h2>Dataset</h2>
  <p>
    The swarm operates on a <strong>1,000-row mock sales dataset</strong> spanning
    the last 90 days across 5 regions and 4 products. In production, swap
    <code style="font-size:0.82rem; color:rgba(255,255,255,0.5); background:rgba(255,255,255,0.06); padding:0.1rem 0.4rem; border-radius:4px;">generate_mock_data()</code>
    with a live SQL query or API call — the swarm pipeline is data-source agnostic.
  </p>

  <div class="cols">
    <div class="col-item">
      <div class="col-name">Date</div>
      <div class="col-type">Last 90 days</div>
    </div>
    <div class="col-item">
      <div class="col-name">Region</div>
      <div class="col-type">N · S · E · W · EMEA</div>
    </div>
    <div class="col-item">
      <div class="col-name">Product</div>
      <div class="col-type">4 product lines</div>
    </div>
    <div class="col-item">
      <div class="col-name">DealValue</div>
      <div class="col-type">$5K – $150K</div>
    </div>
    <div class="col-item">
      <div class="col-name">Status</div>
      <div class="col-type">Won · Lost · Pending</div>
    </div>
  </div>

  <!-- Tech stack -->
  <h2>Tech Stack</h2>
  <div class="stack">
    <span class="tech">Python</span>
    <span class="tech">Streamlit</span>
    <span class="tech">Pandas</span>
    <span class="tech">Plotly</span>
    <span class="tech">Gemini 3.1 Flash Lite</span>
    <span class="tech">OpenRouter</span>
    <span class="tech">OpenAI SDK</span>
  </div>

  <!-- CTA -->
  <div class="cta">
    <a href="#" class="btn btn-solid" onclick="window.top.open('https://www.thecraftsync.com', '_blank'); return false;">Contact Us ↗</a>
    <a href="#" class="btn btn-outline" onclick="window.top.open('https://github.com/professionalbugwriter/demo-agent', '_blank'); return false;">GitHub ↗</a>
  </div>

</div>
</body>
</html>
"""

components.html(PAGE_HTML, height=1400, scrolling=True)
