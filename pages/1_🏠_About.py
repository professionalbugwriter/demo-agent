import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="CraftSync · Chart Agent",
    page_icon="📊",
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
    max-width: 760px;
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
  .brand-info {}
  .brand-name {
    font-size: 1rem; font-weight: 700;
    letter-spacing: 0.06em; text-transform: uppercase;
    color: #fff;
    line-height: 1;
  }
  .brand-url {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.35);
    margin-top: 0.2rem;
    letter-spacing: 0.02em;
  }
  .brand-url a:hover { color: rgba(255,255,255,0.7); }

  /* ── Text content ── */
  h1 {
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    line-height: 1.2;
    color: #fff;
    margin-bottom: 1rem;
  }
  h1 span {
    background: linear-gradient(90deg, #ff3eb5, #a855f7, #22d3ee);
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
  .p1 { color: #ff3eb5; border-color: rgba(255,62,181,0.3); background: rgba(255,62,181,0.07); }
  .p2 { color: #a855f7; border-color: rgba(168,85,247,0.3); background: rgba(168,85,247,0.07); }
  .p3 { color: #22d3ee; border-color: rgba(34,211,238,0.3); background: rgba(34,211,238,0.07); }
  .p4 { color: #fb923c; border-color: rgba(251,146,60,0.3); background: rgba(251,146,60,0.07); }
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
  .col-type {
    font-size: 0.7rem;
    color: rgba(255,255,255,0.25);
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
  <h1>Chart-on-the-Fly <span>Agent</span></h1>

  <p>
    Built by <strong>CraftSync</strong> — strategic design meeting technical precision.
    This is a local, open-source AI agent that generates interactive data visualisations
    directly from natural language. No dropdowns, no config. Just ask.
  </p>

  <p>
    The agent is powered by <strong>Gemini 3.1 Flash Lite</strong> via OpenRouter, using
    function-calling to decide which chart to build, what filters to apply, and how to
    group the data — all from a single plain-English prompt.
  </p>

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
    The agent picks the right chart automatically. Bar charts for comparisons,
    line charts for trends, pie charts for proportions, scatter plots for distribution,
    and KPI cards when you need headline numbers. It can call multiple tools in one
    response when the question calls for it.
  </p>

  <!-- Dataset -->
  <h2>Dataset</h2>
  <p>
    The agent works against a <strong>1,000-row mock sales dataset</strong> spanning
    the last 90 days across 5 regions and 4 products. In production, swap
    <code style="font-size:0.82rem; color:rgba(255,255,255,0.5); background:rgba(255,255,255,0.06); padding:0.1rem 0.4rem; border-radius:4px;">generate_mock_data()</code>
    with a live SQL query or API call.
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

  <!-- CTA -->
  <div class="cta">
    <a href="#" class="btn btn-solid" onclick="window.top.open('https://www.thecraftsync.com', '_blank'); return false;">Contact Us ↗</a>
  </div>

</div>
</body>
</html>
"""

components.html(PAGE_HTML, height=1200, scrolling=True)
