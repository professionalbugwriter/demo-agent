"""
╔══════════════════════════════════════════════════════════════════════════╗
║  tools.py – Chart tool definitions + executor for the KPI Agent        ║
║                                                                          ║
║  Provides:                                                               ║
║    TOOL_SCHEMAS  – OpenAI function-calling schema list                  ║
║    execute_tool  – dispatcher → (plotly_fig | None, text, extras | None)║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import plotly.express as px

# ── Colour palette aligned with the dark-mode UI ─────────────────────────────
PALETTE = ["#63b3ed", "#a78bfa", "#68d391", "#f6ad55", "#fc8181", "#4fd1c5", "#f9a8d4"]

_LAYOUT_BASE = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Inter, sans-serif", size=13),
    legend=dict(
        bgcolor="rgba(255,255,255,0.04)",
        bordercolor="rgba(99,179,237,0.15)",
        borderwidth=1,
        font=dict(color="#94a3b8"),
    ),
    margin=dict(l=40, r=20, t=55, b=40),
    xaxis=dict(
        gridcolor="rgba(99,179,237,0.08)",
        linecolor="rgba(99,179,237,0.15)",
        tickfont=dict(color="#64748b"),
    ),
    yaxis=dict(
        gridcolor="rgba(99,179,237,0.08)",
        linecolor="rgba(99,179,237,0.15)",
        tickfont=dict(color="#64748b"),
    ),
)


def _layout(title: str) -> dict:
    return {
        **_LAYOUT_BASE,
        "title": dict(
            text=title,
            font=dict(color="#f1f5f9", size=15, family="Inter, sans-serif"),
            x=0.01,
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
# TOOL SCHEMAS  (OpenAI / OpenRouter function-calling format)
# ══════════════════════════════════════════════════════════════════════════════

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bar_chart",
            "description": (
                "Generate a bar chart from the sales dataset. "
                "Use to compare revenue or deal counts across Region, Product, or Status. "
                "Supports optional grouped bars."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "x_col": {
                        "type": "string",
                        "enum": ["Region", "Product", "Status"],
                        "description": "Category for the X-axis.",
                    },
                    "y_col": {
                        "type": "string",
                        "enum": ["DealValue", "count"],
                        "description": "'DealValue' sums revenue; 'count' counts deals.",
                    },
                    "group_by": {
                        "type": "string",
                        "enum": ["Region", "Product", "Status", "none"],
                        "description": "Secondary grouping for grouped bars. 'none' = plain bars.",
                    },
                    "filter_region": {
                        "type": "string",
                        "enum": ["North", "South", "East", "West", "EMEA", "all"],
                        "description": "Restrict to a region, or 'all'.",
                    },
                    "filter_status": {
                        "type": "string",
                        "enum": ["Won", "Lost", "Pending", "all"],
                        "description": "Restrict to a deal status, or 'all'.",
                    },
                    "title": {"type": "string", "description": "Chart title."},
                },
                "required": ["x_col", "y_col", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "line_chart",
            "description": (
                "Generate a weekly time-series line chart to visualise trends. "
                "Use for trend analysis over the 90-day window."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "y_col": {
                        "type": "string",
                        "enum": ["DealValue", "count"],
                        "description": "Metric to plot over time.",
                    },
                    "group_by": {
                        "type": "string",
                        "enum": ["Region", "Product", "Status", "none"],
                        "description": "Creates a separate line per group value.",
                    },
                    "filter_region": {
                        "type": "string",
                        "enum": ["North", "South", "East", "West", "EMEA", "all"],
                        "description": "Restrict to a region, or 'all'.",
                    },
                    "filter_status": {
                        "type": "string",
                        "enum": ["Won", "Lost", "Pending", "all"],
                        "description": "Restrict to a deal status, or 'all'.",
                    },
                    "title": {"type": "string", "description": "Chart title."},
                },
                "required": ["y_col", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pie_chart",
            "description": (
                "Generate a donut/pie chart to show proportional distribution. "
                "Use for share-of-revenue or share-of-deals by category."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "label_col": {
                        "type": "string",
                        "enum": ["Region", "Product", "Status"],
                        "description": "Column whose values become pie slices.",
                    },
                    "value_col": {
                        "type": "string",
                        "enum": ["DealValue", "count"],
                        "description": "'DealValue' = revenue share; 'count' = deal share.",
                    },
                    "filter_region": {
                        "type": "string",
                        "enum": ["North", "South", "East", "West", "EMEA", "all"],
                        "description": "Restrict to a region, or 'all'.",
                    },
                    "filter_status": {
                        "type": "string",
                        "enum": ["Won", "Lost", "Pending", "all"],
                        "description": "Restrict to a deal status, or 'all'.",
                    },
                    "title": {"type": "string", "description": "Chart title."},
                },
                "required": ["label_col", "value_col", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scatter_chart",
            "description": (
                "Generate a scatter plot of deal values over time. "
                "Useful for spotting outliers, clustering, or distribution patterns."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "color_col": {
                        "type": "string",
                        "enum": ["Region", "Product", "Status"],
                        "description": "Column used to colour the dots.",
                    },
                    "filter_region": {
                        "type": "string",
                        "enum": ["North", "South", "East", "West", "EMEA", "all"],
                        "description": "Restrict to a region, or 'all'.",
                    },
                    "filter_status": {
                        "type": "string",
                        "enum": ["Won", "Lost", "Pending", "all"],
                        "description": "Restrict to a deal status, or 'all'.",
                    },
                    "title": {"type": "string", "description": "Chart title."},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kpi_summary",
            "description": (
                "Compute KPI metrics: total revenue, win rate, pipeline size, "
                "average deal size. Returns metric cards, not a chart. "
                "Use when the user asks for KPIs, performance overview, or a summary."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_region": {
                        "type": "string",
                        "enum": ["North", "South", "East", "West", "EMEA", "all"],
                        "description": "Region to summarise, or 'all' for the whole dataset.",
                    }
                },
                "required": ["filter_region"],
            },
        },
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# PRIVATE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _filter(df: pd.DataFrame, region: str = "all", status: str = "all") -> pd.DataFrame:
    fdf = df.copy()
    if region and region not in ("all", None):
        fdf = fdf[fdf["Region"] == region]
    if status and status not in ("all", None):
        fdf = fdf[fdf["Status"] == status]
    return fdf


def _aggregate(df: pd.DataFrame, group_cols: list, y_col: str) -> tuple[pd.DataFrame, str]:
    """Aggregate df and return (agg_df, value_column_name)."""
    if y_col == "count":
        agg = df.groupby(group_cols).size().reset_index(name="count")
        return agg, "count"
    agg = df.groupby(group_cols)["DealValue"].sum().reset_index()
    return agg, "DealValue"


# ══════════════════════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS
# ══════════════════════════════════════════════════════════════════════════════

def _bar_chart(args: dict, df: pd.DataFrame):
    x      = args["x_col"]
    y_col  = args.get("y_col", "count")
    grp    = args.get("group_by") or "none"
    region = args.get("filter_region") or "all"
    status = args.get("filter_status") or "all"
    title  = args.get("title", f"{y_col} by {x}")

    fdf   = _filter(df, region, status)
    gcols = [x, grp] if grp != "none" else [x]
    agg, v_key = _aggregate(fdf, gcols, y_col)
    y_label = "Deal Count" if y_col == "count" else "Revenue ($)"

    fig = px.bar(
        agg, x=x, y=v_key,
        color=grp if grp != "none" else None,
        color_discrete_sequence=PALETTE,
        barmode="group",
        labels={v_key: y_label, x: x},
        text_auto=".2s",
    )
    fig.update_traces(marker_line_width=0, textfont_size=11, textfont_color="#e2e8f0")
    fig.update_layout(**_layout(title))

    top = agg[v_key].max()
    return fig, f"Bar chart rendered: {y_label} by {x}. Peak value: {top:,.0f}."


def _line_chart(args: dict, df: pd.DataFrame):
    y_col  = args.get("y_col", "count")
    grp    = args.get("group_by") or "none"
    region = args.get("filter_region") or "all"
    status = args.get("filter_status") or "all"
    title  = args.get("title", "Trend over time")

    fdf = _filter(df, region, status).copy()
    fdf["Date"] = pd.to_datetime(fdf["Date"])
    fdf["Week"] = fdf["Date"].dt.to_period("W").apply(lambda r: r.start_time)

    gcols = ["Week", grp] if grp != "none" else ["Week"]
    agg, v_key = _aggregate(fdf, gcols, y_col)
    y_label = "Deal Count" if y_col == "count" else "Revenue ($)"

    fig = px.line(
        agg, x="Week", y=v_key,
        color=grp if grp != "none" else None,
        color_discrete_sequence=PALETTE,
        markers=True,
        labels={v_key: y_label, "Week": "Week starting"},
    )
    fig.update_traces(line_width=2.5, marker_size=7)
    fig.update_layout(**_layout(title))

    return fig, f"Line chart rendered: {y_label} trend over {len(agg)} weeks."


def _pie_chart(args: dict, df: pd.DataFrame):
    label  = args["label_col"]
    val    = args.get("value_col", "count")
    region = args.get("filter_region") or "all"
    status = args.get("filter_status") or "all"
    title  = args.get("title", f"Distribution by {label}")

    fdf = _filter(df, region, status)
    agg, v_key = _aggregate(fdf, [label], val)
    y_label = "Deal Count" if val == "count" else "Revenue ($)"

    fig = px.pie(
        agg, names=label, values=v_key,
        color_discrete_sequence=PALETTE,
        hole=0.45,
    )
    fig.update_traces(
        textfont_color="#f1f5f9",
        textfont_size=12,
        pull=[0.03] * len(agg),
        hovertemplate="%{label}: %{value:,.0f} (%{percent})<extra></extra>",
    )
    fig.update_layout(**_layout(title))

    total = agg[v_key].sum()
    return fig, f"Pie chart rendered: {y_label} by {label}. Total: {total:,.0f}."


def _scatter_chart(args: dict, df: pd.DataFrame):
    color  = args.get("color_col") or "Region"
    region = args.get("filter_region") or "all"
    status = args.get("filter_status") or "all"
    title  = args.get("title", "Deal Value Distribution")

    fdf = _filter(df, region, status).copy()
    fdf["Date"] = pd.to_datetime(fdf["Date"])

    fig = px.scatter(
        fdf, x="Date", y="DealValue",
        color=color,
        color_discrete_sequence=PALETTE,
        opacity=0.70,
        hover_data=["Region", "Product", "Status", "DealValue"],
        labels={"DealValue": "Deal Value ($)", "Date": "Date"},
    )
    fig.update_traces(marker=dict(size=7, line=dict(width=0)))
    fig.update_layout(**_layout(title))

    return fig, f"Scatter chart rendered: {len(fdf)} deals plotted, coloured by {color}."


def _kpi_summary(args: dict, df: pd.DataFrame):
    region = args.get("filter_region") or "all"
    fdf    = _filter(df, region)

    total  = len(fdf)
    won    = fdf[fdf["Status"] == "Won"]
    lost   = fdf[fdf["Status"] == "Lost"]
    pend   = fdf[fdf["Status"] == "Pending"]

    revenue  = int(won["DealValue"].sum())
    win_rate = round(len(won) / total * 100, 1) if total else 0.0
    avg_deal = int(won["DealValue"].mean()) if len(won) else 0

    metrics = {
        "region":       region,
        "total_deals":  total,
        "total_revenue": revenue,
        "win_rate":     win_rate,
        "won_deals":    len(won),
        "lost_deals":   len(lost),
        "pending_deals": len(pend),
        "avg_deal_size": avg_deal,
    }

    text = (
        f"KPIs for {'All Regions' if region == 'all' else region + ' Region'}:\n"
        f"• Revenue (Won): ${revenue:,}\n"
        f"• Win Rate: {win_rate}% ({len(won)} won / {total} total)\n"
        f"• Pipeline: {len(pend)} pending deals\n"
        f"• Avg Deal Size: ${avg_deal:,}"
    )
    return None, text, metrics


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC DISPATCHER
# ══════════════════════════════════════════════════════════════════════════════

def execute_tool(name: str, args: dict, df: pd.DataFrame):
    """
    Execute a named tool against the DataFrame.

    Returns
    -------
    (plotly_fig | None, summary_text: str, extra_data: dict | None)
    """
    dispatch = {
        "bar_chart":     _bar_chart,
        "line_chart":    _line_chart,
        "pie_chart":     _pie_chart,
        "scatter_chart": _scatter_chart,
        "kpi_summary":   _kpi_summary,
    }
    fn = dispatch.get(name)
    if fn is None:
        return None, f"Unknown tool: {name}", None

    result = fn(args, df)
    # kpi_summary returns 3 values; chart tools return 2
    if len(result) == 3:
        return result
    return result[0], result[1], None
