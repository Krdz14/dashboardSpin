"""Spin · Who to contact next month (Team 5) — dashboard layout (v3).

Run from the repository root:
    streamlit run dashboard/app.py
Data files are produced by Team5_Model_Experiments_v2.ipynb (dashboard/data/).
Previous versions: dashboard/backup/app_v1_technical.py, dashboard/backup/app_v2_plain.py.
"""
import base64
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

HERE = Path(__file__).parent
DATA = HERE / "data"
LOGO = HERE / "assets/spin_logo.png"
st.set_page_config(page_title="Spin Dashboard", page_icon=str(LOGO), layout="wide")

# ---------------------------------------------------------------- design tokens (Spin brand purple & white)
P900, P700, P600, P500, P400, P300, P200, P100, P50 = (
    "#2E0A63", "#4C0FA3", "#6213CF", "#7A3BE0", "#9466EA", "#B193F0", "#D2C2F7", "#EEE7FC", "#F7F3FE")
ORANGE = "#FF6002"  # Spin brand accent — used sparingly (baselines, markers)
P600_RGB = "98,19,207"
INK, SUB, LINE, GRID, CANVAS = "#111827", "#6B7280", "#E7E5EF", "#F1F0F5", "#F7F6FB"
GRAY = "#CBD0D8"
UP_BG, UP_FG, DN_BG, DN_FG = "#DCFCE7", "#15803D", "#FEE2E2", "#B91C1C"
SEQ = [P700, P500, P300, P200, "#9CA3AF", "#D1D5DB", P100]  # categorical for the 7 groups

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea { font-family: 'Inter', sans-serif; }
.stApp { background: CANVAS; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
.block-container { max-width: 1440px; padding: 2.2rem 2.6rem 3rem 2.6rem; }
h1, h2, h3 { letter-spacing: -0.3px; }

/* ---------- sidebar */
section[data-testid="stSidebar"] { background: #fff; border-right: 1px solid LINE; }
section[data-testid="stSidebar"] .block-container, section[data-testid="stSidebar"] > div { padding-top: 1.2rem; }
.brand { font-weight: 800; font-size: 1.6rem; letter-spacing: -0.5px; color: P600; display:flex; align-items:center; gap:.6rem; }
.brand img { width: 38px; height: 38px; border-radius: 10px; }
.sec { display:flex; align-items:baseline; gap:.6rem; margin: .4rem 0 -.6rem 0; }
.sec b { font-size: 1.02rem; color: INK; } .sec span { color: SUB; font-size: .84rem; }
.brand .dot { width: 28px; height: 28px; border-radius: 8px; background: P600; display:inline-flex; align-items:center;
              justify-content:center; color:#fff; font-size: .9rem; }
.brand-sub { color: SUB; font-size: .82rem; margin: .2rem 0 1.4rem 0; }
section[data-testid="stSidebar"] [role="radiogroup"] { gap: 4px; width: 100%; }
section[data-testid="stSidebar"] [data-testid="stRadioOption"] { padding: .62rem .8rem; border-radius: 8px; width: 100%;
    margin: 0; cursor: pointer; transition: background .15s; }
section[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover { background: P50; }
section[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]) { display: none; }
section[data-testid="stSidebar"] [data-testid="stRadioOption"] p { font-size: .98rem; font-weight: 500; color: #374151;
    display: flex; align-items: center; gap: .6rem; }
section[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] { background: P100; }
section[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] p { color: P700; font-weight: 600; }
.side-note { color: SUB; font-size: .82rem; line-height: 1.55; border-top: 1px solid LINE; padding-top: 1rem; margin-top: 1rem; }
.side-note b { color: INK; }

/* ---------- page header */
.ph-title { font-size: 1.85rem; font-weight: 700; color: INK; margin: 0; line-height: 1.2; }
.ph-sub { color: SUB; font-size: .98rem; margin-top: .25rem; }

/* ---------- KPI cards */
.kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px; margin: 1.4rem 0 1.25rem 0; }
@media (max-width: 1100px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px)  { .kpis { grid-template-columns: 1fr; } }
.kpi { background: #fff; border: 1px solid LINE; border-radius: 12px; padding: 1.15rem 1.3rem; }
.kpi .ic { width: 36px; height: 36px; border-radius: 50%; background: P100; color: P600; display:flex;
           align-items:center; justify-content:center; margin-bottom: .8rem; }
.kpi .lbl { color: #4B5563; font-size: .92rem; font-weight: 500; }
.kpi .row { display:flex; align-items:center; gap:.6rem; margin-top:.25rem; flex-wrap: wrap; }
.kpi .val { font-size: 1.95rem; font-weight: 700; color: INK; letter-spacing: -0.5px; line-height: 1.2; }
.kpi .sub { color: SUB; font-size: .8rem; margin-top: .3rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.badge { display:inline-flex; align-items:center; gap:3px; padding: 2px 9px; border-radius: 999px; font-size: .76rem; font-weight: 600; }
.badge.up { background: UP_BG; color: UP_FG; } .badge.dn { background: DN_BG; color: DN_FG; }
.badge.nt { background: P100; color: P700; }

/* ---------- cards (st.container(key="card_...")) */
div[class*="st-key-card"] { background: #fff; border: 1px solid LINE; border-radius: 12px; padding: 1.15rem 1.3rem 1rem 1.3rem; }
/* cards side by side in one row get the same height */
[data-testid="stColumn"]:has([class*="st-key-card"]) > [data-testid="stVerticalBlock"],
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:has(> [class*="st-key-card"]),
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] > [class*="st-key-card"] { height: 100%; }
div[class*="st-key-card"] { box-sizing: border-box; padding-bottom: 1.3rem; }
.legend { padding-bottom: .4rem; }
.ch-title { font-size: 1.05rem; font-weight: 600; color: INK; }
.ch-sub { color: SUB; font-size: .84rem; margin-top: 2px; margin-bottom: .4rem; }

/* list rows (like "Highest tickets" / "Top usage method") */
.lrow { display:flex; justify-content:space-between; align-items:center; padding: .62rem .2rem; border-bottom: 1px solid GRID; }
.lrow:last-child { border-bottom: none; }
.lrow .nm { font-weight: 600; color: INK; font-size: .95rem; }
.lrow .ds { color: SUB; font-size: .82rem; margin-top: 2px; }
.lrow .vl { color: #374151; font-size: .92rem; font-weight: 500; white-space: nowrap; padding-left: 1rem; }
.bar { height: 6px; background: GRID; border-radius: 99px; margin-top: 6px; overflow: hidden; }
.bar > span { display:block; height: 100%; background: P500; border-radius: 99px; }
.legend { display:flex; flex-direction:column; gap:.55rem; margin-top:.3rem; }
.legend div { display:flex; align-items:center; gap:.55rem; font-size:.88rem; color:#374151; }
.legend i { width:10px; height:10px; border-radius:50%; display:inline-block; flex: none; }
.legend b { margin-left:auto; color: INK; }
.chip { display:inline-block; padding: 3px 11px; border-radius: 999px; font-size: .82rem; margin: 3px 4px 3px 0; font-weight: 500; }
.chip.hi { background: P100; color: P700; } .chip.lo { background: #F3F4F6; color: #4B5563; }
.action { background: P50; border-left: 3px solid P500; border-radius: 6px; padding: .8rem 1rem; color: #374151;
          font-size: .92rem; line-height: 1.55; margin-top: .8rem; }

/* buttons */
.stDownloadButton button, .stButton button { border-radius: 8px; font-weight: 600; padding: .5rem 1.1rem; }
.stButton button[kind="primary"] { background: P600; border-color: P600; }
.stButton button[kind="primary"]:hover { background: P700; border-color: P700; }
[data-testid="stElementToolbar"] { display: none; }
</style>
"""
for k, v in dict(CANVAS=CANVAS, LINE=LINE, GRID=GRID, INK=INK, SUB=SUB, UP_BG=UP_BG, UP_FG=UP_FG, DN_BG=DN_BG,
                 DN_FG=DN_FG, P700=P700, P600=P600, P500=P500, P100=P100, P50=P50).items():
    CSS = CSS.replace(k, v)
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------- icons (inline SVG, stroke = currentColor)
_I = {
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "cart": '<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.7 13.4a2 2 0 0 0 2 1.6h9.7a2 2 0 0 0 2-1.6L23 6H6"/>',
    "refresh": '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>',
    "store": '<path d="M3 9l1-5h16l1 5"/><path d="M4 9v11h16V9"/><path d="M9 20v-6h6v6"/>',
    "layers": '<path d="M12 2 2 7l10 5 10-5-10-5z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "trend": '<path d="m23 6-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/>',
    "check": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4 12 14.01l-3-3"/>',
    "send": '<path d="m22 2-7 20-4-9-9-4 20-7z"/>',
}


def icon(name, size=18):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{_I[name]}</svg>')


# ---------------------------------------------------------------- UI helpers
def pct(x, d=0): return f"{x * 100:.{d}f}%"
def month_name(s): return pd.Timestamp(s + "-01").strftime("%B %Y")


def badge(text, kind="nt"):
    arrow = {"up": "↑ ", "dn": "↓ "}.get(kind, "")
    return f"<span class='badge {kind}'>{arrow}{text}</span>"


def delta_badge(change, text, higher_is_good=True):
    """Green when the move is good, red when it is bad — regardless of direction."""
    good = (change >= 0) == higher_is_good
    cls = "up" if good else "dn"
    arrow = "↑ " if change >= 0 else "↓ "
    return f"<span class='badge {cls}'>{arrow}{text}</span>"


def kpi_row(items):
    """items: list of (icon, label, value, badge_html, sub)."""
    cells = "".join(
        f"<div class='kpi'><div class='ic'>{icon(ic)}</div><div class='lbl'>{lbl}</div>"
        f"<div class='row'><span class='val'>{val}</span>{bdg}</div><div class='sub'>{sub}</div></div>"
        for ic, lbl, val, bdg, sub in items)
    st.markdown(f"<div class='kpis'>{cells}</div>", unsafe_allow_html=True)


def page_header(title, sub, right=None):
    l, r = st.columns([3, 1.3], vertical_alignment="center")
    l.markdown(f"<div class='ph-title'>{title}</div><div class='ph-sub'>{sub}</div>", unsafe_allow_html=True)
    if right:
        with r:
            right()


def card_head(title, sub=""):
    st.markdown(f"<div class='ch-title'>{title}</div><div class='ch-sub'>{sub}</div>", unsafe_allow_html=True)


_card_n = [0]


def card():
    _card_n[0] += 1
    return st.container(key=f"card_{_card_n[0]}")


def style(fig, h=320, legend=False):
    fig.update_layout(template="plotly_white", height=h, showlegend=legend, margin=dict(l=4, r=12, t=8, b=4),
                      font=dict(family="Inter, sans-serif", size=12.5, color="#4B5563"),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      hoverlabel=dict(bgcolor="white", bordercolor=LINE, font=dict(color=INK)),
                      legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, font=dict(size=12.5)))
    if legend:
        fig.update_layout(margin=dict(t=36))
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=LINE, ticks="")
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, ticks="")
    return fig


def chart(fig):
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def donut(labels, values, colors, center_big, center_small, h=250):
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.72, sort=False, direction="clockwise",
                           marker=dict(colors=colors, line=dict(color="#fff", width=2)), textinfo="none",
                           hovertemplate="%{label}<br>%{value:,} · %{percent}<extra></extra>"))
    fig.add_annotation(text=f"<b style='font-size:22px;color:{INK}'>{center_big}</b><br>"
                            f"<span style='font-size:12px;color:{SUB}'>{center_small}</span>", showarrow=False)
    return style(fig, h)


def legend_html(rows):
    """rows: list of (color, name, value_text)."""
    return "<div class='legend'>" + "".join(
        f"<div><i style='background:{c}'></i>{n}<b>{v}</b></div>" for c, n, v in rows) + "</div>"


# ---------------------------------------------------------------- plain-language vocabulary
CAMPAIGN = {
    "Flip-Out": dict(key="flip_out", short="Move spend outside OXXO", people="users who move their spending outside OXXO",
                     icon="cart", offer="an offer to shop outside OXXO",
                     meaning="Users who start buying more at other stores (not OXXO) for two months in a row."),
    "Flip-In": dict(key="flip_in", short="Win back quiet users", people="quiet users who come back to the card",
                    icon="refresh", offer="a win-back offer",
                    meaning="Users who had slowed down and go back to their usual number of card purchases for two months in a row."),
}
TRAIT = {
    "oxxo_share": ("Shops a lot at OXXO", "Rarely shops at OXXO"),
    "ecommerce_share": ("Buys a lot online", "Rarely buys online"),
    "virtual_card_share": ("Uses the virtual card a lot", "Rarely uses the virtual card"),
    "intl_share": ("Often buys from international sites", "Rarely buys abroad"),
    "cash_funding_share": ("Loads money with cash", "Rarely loads cash"),
    "spei_funding_share": ("Loads money by bank transfer", "Rarely uses bank transfers"),
    "zero_funding_share": ("Often spends without topping up", "Tops up most months"),
    "monthly_spend": ("Spends more than most", "Spends less than most"),
    "active_months_share": ("Uses the card every month", "Uses the card only some months"),
    "decline_rate": ("Many payments get declined", "Few payments get declined"),
}
HABIT = {"oxxo_share": "OXXO", "ecommerce_share": "Online", "virtual_card_share": "Virtual card",
         "intl_share": "International", "cash_funding_share": "Cash top-ups", "spei_funding_share": "Bank transfers",
         "zero_funding_share": "No top-up", "monthly_spend": "Monthly spend", "active_months_share": "Active months",
         "decline_rate": "Declines"}


def traits(row, n=3):
    z = {f: row[f"z_{f}"] for f in TRAIT}
    top = [f for f in sorted(z, key=lambda f: -abs(z[f])) if abs(z[f]) >= 0.3][:n]
    return [(TRAIT[f][0] if z[f] > 0 else TRAIT[f][1], z[f] > 0) for f in top]


def level(ratio):
    if ratio >= 1.1: return "Higher than average", "hi"
    if ratio <= 0.9: return "Lower than average", "lo"
    return "About average", "lo"


def capture_curve(y, s):
    order = np.argsort(-s); y = np.asarray(y)[order]
    return np.arange(1, len(y) + 1) / len(y), np.cumsum(y) / max(y.sum(), 1)


# ---------------------------------------------------------------- data
@st.cache_data
def load():
    card_ = json.loads((DATA / "model_card.json").read_text())
    live_ = pd.read_csv(DATA / "live_users.csv")
    bt_ = pd.read_csv(DATA / "backtest_may2026.csv")
    prof_ = pd.read_csv(DATA / "persona_profiles.csv")
    mon_ = pd.read_csv(DATA / "monthly.csv", parse_dates=["mes"])
    log_ = pd.read_csv(DATA / "experiment_log.csv")
    kpi_ = pd.read_csv(DATA / "kpi_monthly.csv", parse_dates=["mes"])  # built by dashboard/build_kpis.py
    base_ = json.loads((DATA / "kpi_baseline.json").read_text())
    return card_, live_, bt_, prof_, mon_, log_, kpi_, base_


mc, live, bt, prof, mon, log, kpi, base = load()
BASE = base["values"]
BASE_LO, BASE_HI = (pd.Period(m) for m in base["window"])
BASE_LABEL = f"{BASE_LO.strftime('%b')}–{BASE_HI.strftime('%b %Y')}"
LOGO_B64 = base64.b64encode(LOGO.read_bytes()).decode()
NO_GROUP = "No group yet (new user)"
avg_rate = {ev: bt[bt.event == ev].y.mean() for ev in CAMPAIGN}
GROUP_COLOR = dict(zip(prof.sort_values("users", ascending=False).name, SEQ))
GROUP_COLOR[NO_GROUP] = "#E5E7EB"


# ---------------------------------------------------------------- sidebar
PAGES = {"Overview": ":material/dashboard:", "Customer groups": ":material/groups:",
         "Who to contact": ":material/campaign:", "Model quality": ":material/verified:"}
st.session_state.setdefault("nav", "Overview")
with st.sidebar:
    st.markdown(f"<div class='brand'><img src='data:image/png;base64,{LOGO_B64}' alt=''>SPIN</div>"
                f"<div class='brand-sub'>Campaign dashboard · Team 5</div>", unsafe_allow_html=True)
    page = st.radio("Navigation", list(PAGES), key="nav", label_visibility="collapsed",
                    format_func=lambda p: f"{PAGES[p]} {p}")
    st.markdown(
        f"<div class='side-note'>Data up to <b>{month_name(mc['data_until'])}</b><br>Updated {mc['generated']}<br><br>"
        f"<b>Flip-Out</b> · {CAMPAIGN['Flip-Out']['meaning']}<br><br>"
        f"<b>Flip-In</b> · {CAMPAIGN['Flip-In']['meaning']}</div>", unsafe_allow_html=True)


def go_to(p): st.session_state.nav = p


# ================================================================ OVERVIEW
if page == "Overview":
    page_header("Overview", f"Campaign targeting for next month · data up to {month_name(mc['data_until'])}")

    last, prev = mon.iloc[-1], mon.iloc[-2]
    first = mon.iloc[0]
    n_out, n_in = int(live.flip_out_eligible.sum()), int(live.flip_in_eligible.sum())
    au_chg = last.active_users / prev.active_users - 1
    ox_chg = last.oxxo_share - first.oxxo_share
    rated = mon.dropna(subset=["flip_out_rate"])
    fo_chg = rated.iloc[-1].flip_out_rate - rated.iloc[0].flip_out_rate
    kpi_row([
        ("users", "Active users", f"{int(last.active_users):,}", delta_badge(au_chg, pct(abs(au_chg), 1)),
         f"vs {prev.mes:%B} · {last.mes:%B %Y}"),
        ("store", "Purchases at OXXO", pct(last.oxxo_share, 1), delta_badge(ox_chg, f"{abs(ox_chg) * 100:.1f} pp", False),
         f"since {first.mes:%b %Y}"),
        ("cart", "Flip-Out audience", f"{n_out:,}", badge(f"{pct(n_out / len(live))} of users"),
         "users who can get a non-OXXO offer"),
        ("refresh", "Flip-In audience", f"{n_in:,}", badge(f"{pct(n_in / len(live))} of users"),
         "quiet users who can be won back"),
    ])

    # ---- baseline KPIs: main number = fixed baseline window; badge = latest month vs that baseline
    k_last = kpi.iloc[-1]
    lm = f"{k_last.mes:%b %Y}"

    def vs_base(key, rel=False):
        d = k_last[key] - BASE[key]
        return delta_badge(d, f"{abs(d / BASE[key]) * 100:.1f}%" if rel else f"{abs(d) * 100:.1f} pp")

    st.markdown(f"<div class='sec'><b>Baseline KPIs</b><span>{BASE_LABEL} average per active user · "
                f"badge = {lm} vs baseline</span></div>", unsafe_allow_html=True)
    kpi_row([
        ("store", "External spending ratio", pct(BASE["ext_ratio"], 1), vs_base("ext_ratio"),
         "share of purchases outside OXXO"),
        ("trend", "Average TPV per user", f"${BASE['tpv_mean']:,.0f}", vs_base("tpv_mean", rel=True),
         f"MXN per month · median ${BASE['tpv_median']:,.0f}"),
        ("layers", "Multi-merchant rate", pct(BASE["mm_rate"], 1), vs_base("mm_rate"),
         "active users buying at 2+ merchants"),
        ("target", "Multi-merchant activation", pct(BASE["mm_activation"], 1), vs_base("mm_activation"),
         "0–1 merchants → 2+ the next month"),
    ])

    c1, c2 = st.columns([2.05, 1], gap="medium")
    with c1, card():
        h, s = st.columns([3, 1.1], vertical_alignment="center")
        # name: (data, column, number format, is %, has baseline)
        METRICS = {"External spending ratio": (kpi, "ext_ratio", ".1%", True, True),
                   "Average TPV per user": (kpi, "tpv_mean", "$,.0f", False, True),
                   "Multi-merchant rate": (kpi, "mm_rate", ".1%", True, True),
                   "Multi-merchant activation": (kpi, "mm_activation", ".1%", True, True),
                   "Active users": (mon, "active_users", ",.0f", False, False),
                   "OXXO purchase share": (mon, "oxxo_share", ".1%", True, False),
                   "Flip-Out rate": (mon, "flip_out_rate", ".1%", True, False),
                   "Flip-In rate": (mon, "flip_in_rate", ".1%", True, False)}
        with s:
            m = st.selectbox("Metric", list(METRICS), label_visibility="collapsed")
        src, col, fmt, is_pct, has_base = METRICS[m]
        with h:
            card_head(f"{m} over time", f"Monthly trend · shaded = baseline window ({BASE_LABEL})" if has_base else "Monthly trend")
        d = src.dropna(subset=[col])
        lo, hi = d[col].min(), d[col].max()
        pad = (hi - lo) * 0.6 or hi * 0.1
        fig = go.Figure()
        fig.add_scatter(x=d.mes, y=d[col], mode="lines+markers", line=dict(color=P600, width=2.5, shape="spline"),
                        marker=dict(size=6, color=P600), fill="tozeroy", fillcolor=f"rgba({P600_RGB},0.08)",
                        name=m, hovertemplate=f"%{{x|%b %Y}} · %{{y:{fmt}}}<extra></extra>")
        if has_base:
            fig.add_vrect(x0=BASE_LO.start_time - pd.Timedelta(days=15), x1=BASE_HI.start_time + pd.Timedelta(days=15),
                          fillcolor=ORANGE, opacity=0.07, line_width=0)
            fig.add_hline(y=BASE[col], line_dash="dash", line_color=ORANGE, line_width=1.5,
                          annotation_text=f"baseline {format(BASE[col], fmt.replace('$', ''))}" if is_pct
                          else f"baseline ${BASE[col]:,.0f}" if fmt.startswith("$") else "baseline",
                          annotation_font_color=ORANGE, annotation_position="top left")
        else:
            fig.add_hline(y=d[col].mean(), line_dash="dot", line_color=P300, annotation_text="average",
                          annotation_font_color=SUB, annotation_position="top left")
        fig.update_yaxes(range=[max(lo - pad, 0), hi + pad * 0.5],
                         tickformat=".0%" if is_pct else "$,.0f" if fmt.startswith("$") else ",.0f")
        fig.update_xaxes(dtick="M1", tickformat="%b<br>%Y")
        chart(style(fig, 410))

    with c2, card():
        card_head("Customer groups", "Share of users by behavior segment")
        g = prof.sort_values("users", ascending=False)
        chart(donut(g.name, g.users, [GROUP_COLOR[n] for n in g.name], f"{int(g.users.sum() / 1000)}k", "users", 230))
        st.markdown(legend_html([(GROUP_COLOR[n], n, pct(s)) for n, s in zip(g.name, g.share_users)]),
                    unsafe_allow_html=True)

    c3, c4 = st.columns([2.05, 1], gap="medium")
    with c3, card():
        h, b_ = st.columns([3, 1.1], vertical_alignment="center")
        with h:
            card_head("Best groups for Flip-Out", "Share of each group that moved spend outside OXXO (Jun–Jul 2026)")
        b_.button("View groups", width="stretch", on_click=go_to, args=("Customer groups",))
        rates = bt[bt.event == "Flip-Out"].groupby("persona_name").y.mean().sort_values()
        top2 = rates.nlargest(2).min()
        fig = go.Figure(go.Bar(x=rates.values, y=rates.index, orientation="h",
                               marker=dict(color=[P600 if r >= top2 else P200 for r in rates.values], cornerradius=4),
                               text=[pct(r, 1) for r in rates.values], textposition="outside", cliponaxis=False,
                               hovertemplate="%{y}: %{x:.1%}<extra></extra>"))
        fig.add_vline(x=avg_rate["Flip-Out"], line_dash="dot", line_color=SUB,
                      annotation_text=f"avg {pct(avg_rate['Flip-Out'], 1)}", annotation_font_color=SUB,
                      annotation_position="bottom right")
        fig.update_xaxes(visible=False, range=[0, rates.max() * 1.18])
        fig.update_yaxes(showgrid=False)
        chart(style(fig, 400))

    with c4, card():
        card_head("Share of total spend", "Which groups move the money")
        g = prof.sort_values("share_spend", ascending=False)
        mx = g.share_spend.max()
        st.markdown("".join(
            f"<div class='lrow' style='display:block'><div style='display:flex;justify-content:space-between'>"
            f"<span class='nm'>{n}</span><span class='vl'>{pct(s, 1)}</span></div>"
            f"<div class='bar'><span style='width:{s / mx * 100:.0f}%'></span></div></div>"
            for n, s in zip(g.name, g.share_spend)), unsafe_allow_html=True)

# ================================================================ CUSTOMER GROUPS
elif page == "Customer groups":
    page_header("Customer groups", "7 segments of users with similar habits — where they shop, how they top up, how much they spend")

    big = prof.loc[prof.users.idxmax()]
    fo = prof.loc[prof.flip_out_rate_may.idxmax()]
    fi = prof.loc[prof.flip_in_rate_may.idxmax()]
    kpi_row([
        ("layers", "Customer groups", f"{len(prof)}", badge(f"{int(prof.users.sum()):,} users"), "built from 10 spending habits"),
        ("users", "Largest group", pct(big.share_users), badge(f"{int(big.users):,} users"), big["name"]),
        ("cart", "Best Flip-Out group", pct(fo.flip_out_rate_may), delta_badge(1, f"{fo.flip_out_rate_may / avg_rate['Flip-Out']:.1f}× avg"),
         fo["name"]),
        ("refresh", "Best Flip-In group", pct(fi.flip_in_rate_may), delta_badge(1, f"{fi.flip_in_rate_may / avg_rate['Flip-In']:.1f}× avg"),
         fi["name"]),
    ])

    order = prof.sort_values("users", ascending=False)
    name = st.pills("Group", list(order.name), default=order.name.iloc[0], label_visibility="collapsed") or order.name.iloc[0]
    r = prof[prof.name == name].iloc[0]

    c1, c2 = st.columns([1.15, 1], gap="medium")
    with c1, card():
        card_head(name, f"{int(r.users):,} users · {pct(r.share_users)} of users · {pct(r.share_spend)} of total spend")
        chips = "".join(f"<span class='chip {'hi' if up else 'lo'}'>{t}</span>" for t, up in traits(r))
        st.markdown(f"<div>{chips}</div><div class='action'><b>What to offer them</b><br>{r.action}</div>",
                    unsafe_allow_html=True)
        rows = []
        for ev, col in (("Flip-Out", "flip_out_rate_may"), ("Flip-In", "flip_in_rate_may")):
            txt, cls = level(r[col] / avg_rate[ev])
            rows.append(f"<div class='lrow'><div><div class='nm'>{CAMPAIGN[ev]['short']}</div>"
                        f"<div class='ds'>{pct(r[col], 1)} vs {pct(avg_rate[ev], 1)} average</div></div>"
                        f"<span class='chip {cls}'>{txt}</span></div>")
        st.markdown("<div style='margin-top:.6rem'>" + "".join(rows) + "</div>", unsafe_allow_html=True)

    with c2, card():
        card_head("Habits vs. the average user", "How far above (+) or below (−) average this group is")
        z = pd.Series({HABIT[f]: r[f"z_{f}"] for f in TRAIT}).clip(-2, 3).sort_values()
        fig = go.Figure(go.Bar(x=z.values, y=z.index, orientation="h",
                               marker=dict(color=[P600 if v > 0 else GRAY for v in z.values], cornerradius=3),
                               hovertemplate="%{y}: %{x:+.2f} sd<extra></extra>"))
        fig.add_vline(x=0, line_color=LINE)
        fig.update_xaxes(visible=False)
        fig.update_yaxes(showgrid=False)
        chart(style(fig, 330))

    with card():
        card_head("All groups compared", "Purple = does it more than the average user · gray = less")
        Z = prof.set_index("name")[[f"z_{f}" for f in TRAIT]].clip(-1.5, 1.5)
        Z.columns = [HABIT[f] for f in TRAIT]
        fig = go.Figure(go.Heatmap(z=Z.values, x=Z.columns, y=Z.index, zmid=0, showscale=False, xgap=3, ygap=3,
                                   colorscale=[[0, "#9CA3AF"], [0.5, "#FFFFFF"], [1, P600]],
                                   hovertemplate="%{y}<br>%{x}: %{z:+.2f} sd<extra></extra>"))
        fig.update_xaxes(side="top")
        fig.update_yaxes(showgrid=False)
        chart(style(fig, 330))

    with card():
        card_head("Group summary", "Size and campaign potential of every group")
        tbl = order.assign(**{
            "Flip-Out rate": order.flip_out_rate_may, "Flip-In rate": order.flip_in_rate_may,
            "What defines them": [" · ".join(t for t, _ in traits(row, 2)) for _, row in order.iterrows()]},
        ).rename(columns={"name": "Group", "users": "Users", "share_users": "Share of users", "share_spend": "Share of spend"})
        st.dataframe(tbl[["Group", "Users", "Share of users", "Share of spend", "Flip-Out rate", "Flip-In rate", "What defines them"]],
                     hide_index=True, width="stretch", column_config={
                         "Share of users": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=float(order.share_users.max())),
                         "Share of spend": st.column_config.NumberColumn(format="percent"),
                         "Flip-Out rate": st.column_config.NumberColumn(format="percent"),
                         "Flip-In rate": st.column_config.NumberColumn(format="percent"),
                         "Users": st.column_config.NumberColumn(format="%d")})

# ================================================================ WHO TO CONTACT
elif page == "Who to contact":
    page_header("Who to contact", f"Ranked list for next month · based on data up to {month_name(mc['live_month'])}")

    with card():
        a, b, c = st.columns([1.2, 1, 1.5], gap="large")
        with a:
            camp = st.segmented_control("Campaign", list(CAMPAIGN), default="Flip-Out",
                                        format_func=lambda k: CAMPAIGN[k]["short"]) or "Flip-Out"
        cfg = CAMPAIGN[camp]; k = cfg["key"]
        pool = live[live[f"{k}_eligible"]].copy()
        pool["persona_name"] = pool.persona_name.fillna(NO_GROUP)
        with b:
            cap = st.slider("Share of eligible users to contact", 5, 30, 10, step=5, format="%d%%")
        with c:
            groups = sorted(pool.persona_name.unique(), key=lambda n: (n == NO_GROUP, n))
            sel = st.multiselect("Customer groups", groups, default=groups, placeholder="All groups")
        st.caption(cfg["meaning"])

    if not sel:
        st.warning("Pick at least one customer group.")
        st.stop()

    flt = pool[pool.persona_name.isin(sel)].sort_values(f"{k}_score", ascending=False)
    n_contact = int(round(cap / 100 * len(flt)))
    b = bt[(bt.event == camp) & bt.persona_name.isin(sel)]
    ok = len(b) and b.y.sum() > 0 and n_contact > 0
    if ok:
        x, cum = capture_curve(b.y.values, b.score.values)
        i = max(int(round(cap / 100 * len(b))) - 1, 0)
        found, gain = cum[i], cum[i] / (cap / 100)
    kpi_row([
        ("users", "Eligible users", f"{len(flt):,}", badge(f"{len(sel)} groups"), f"can receive {cfg['offer']}"),
        ("send", "Users to contact", f"{n_contact:,}", badge(f"top {cap}%"), "highest scores first"),
        ("target", "Right people found", pct(found) if ok else "—", delta_badge(1, f"vs {cap}% random") if ok else "",
         "tested on past data (Jun–Jul 2026)"),
        ("trend", "Better than random", f"{gain:.1f}×" if ok else "—",
         delta_badge(gain - 1, f"{(gain - 1) * 100:.0f}%") if ok else "", "lift at the chosen cut-off"),
    ])

    c1, c2 = st.columns([2.05, 1], gap="medium")
    with c1, card():
        card_head("How many of the right people we find", "Contacting more of the ranked list vs picking at random")
        if ok:
            step = max(len(x) // 300, 1)
            fig = go.Figure()
            fig.add_scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(color=GRAY, dash="dot"), name="Random pick",
                            hoverinfo="skip")
            fig.add_scatter(x=x[::step], y=cum[::step], mode="lines", line=dict(color=P600, width=3), name="Our ranked list",
                            fill="tonexty", fillcolor="rgba(98,19,207,0.07)",
                            hovertemplate="Contact %{x:.0%} → find %{y:.0%}<extra></extra>")
            fig.add_scatter(x=[cap / 100], y=[found], mode="markers", marker=dict(size=13, color=ORANGE, line=dict(color="#fff", width=2)),
                            name="Your cut-off", hovertemplate=f"Top {cap}% → {pct(found)}<extra></extra>")
            fig.update_xaxes(title="Share of users contacted", tickformat=".0%")
            fig.update_yaxes(title="Share of right people found", tickformat=".0%")
            chart(style(fig, 420, legend=True))
        else:
            st.info("Not enough past data for this selection.")

    with c2, card():
        card_head("Who is on the list", f"{n_contact:,} users by customer group")
        comp = flt.head(n_contact).persona_name.value_counts()
        if len(comp):
            chart(donut(comp.index, comp.values, [GROUP_COLOR.get(n, P100) for n in comp.index],
                        f"{n_contact:,}", "users", 230))
            st.markdown(legend_html([(GROUP_COLOR.get(n, P100), n, pct(v / n_contact)) for n, v in comp.items()]),
                        unsafe_allow_html=True)

    with card():
        out = flt.head(n_contact).copy()
        out["Priority"] = pd.cut(np.arange(len(out)) / max(len(out), 1), [-1, 1 / 3, 2 / 3, 2],
                                 labels=["Highest", "High", "Good"]).astype(str)
        show = out.rename(columns={"userId": "User ID", "persona_name": "Customer group", "oxxo_share": "Purchases at OXXO",
                                   "ecommerce_share": "Online purchases", "monthly_spend": "Monthly spend (MXN)",
                                   f"{k}_score": "Score"})
        show.insert(0, "#", np.arange(1, len(show) + 1))
        all_cols = ["#", "User ID", "Priority", "Customer group", "Score", "Purchases at OXXO", "Online purchases", "Monthly spend (MXN)"]
        h, t, d = st.columns([2.6, 1, 1], vertical_alignment="center")
        with h:
            card_head(f"Contact list · {n_contact:,} users", "Tip: hold out a random 10% without the offer to measure the real effect")
        more = t.toggle("Spending details", value=False)
        d.download_button("Download CSV", show[all_cols].to_csv(index=False).encode(), f"spin_{k}_top{cap}pct.csv",
                          "text/csv", icon=":material/download:", type="primary", width="stretch")
        cols = all_cols if more else all_cols[:5]
        st.dataframe(show[cols], hide_index=True, width="stretch", height=420, column_config={
            "#": st.column_config.NumberColumn(width="small"),
            "Score": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=float(show.Score.max() or 1)),
            "Purchases at OXXO": st.column_config.NumberColumn(format="percent"),
            "Online purchases": st.column_config.NumberColumn(format="percent"),
            "Monthly spend (MXN)": st.column_config.NumberColumn(format="$%.0f")})

# ================================================================ MODEL QUALITY
else:
    page_header("Model quality", "Tested on May 2026 — a month the model never saw while training")

    ev = mc["events"]
    items = []
    for name_, e in ev.items():
        o, v1 = e["oot"], e["v1_oot"]
        v1_lift = v1["capture10"] / 0.10
        items.append((CAMPAIGN[name_]["icon"], f"{name_} · lift at top 10%", f"{o['lift10']:.2f}×",
                      delta_badge(o["lift10"] - v1_lift, f"{abs(o['lift10'] - v1_lift):.2f} vs v1"), f"{e['version']} · {e['model']}"))
        items.append(("target", f"{name_} · found in top 10%", pct(o["capture10"], 1),
                      delta_badge(o["capture10"] - v1["capture10"], f"{abs(o['capture10'] - v1['capture10']) * 100:.1f} pp vs v1"),
                      "random picking finds 10%"))
    kpi_row([items[0], items[1], items[2], items[3]])

    cols = st.columns(2, gap="medium")
    for col, (name_, e) in zip(cols, ev.items()):
        cfg, lift, cap10 = CAMPAIGN[name_], e["oot"]["lift10"], e["oot"]["capture10"]
        verdict, kind = (("Strong", "up") if lift >= 2 else ("Useful", "nt") if lift >= 1.5 else ("Weak · use with care", "dn"))
        with col, card():
            h, v = st.columns([3, 1.2], vertical_alignment="center")
            with h:
                card_head(f"{name_} · {cfg['short']}", f"Contacting the top 10% finds {pct(cap10)} of the {cfg['people']}")
            v.markdown(f"<div style='text-align:right'><span class='badge {kind}'>{verdict}</span></div>", unsafe_allow_html=True)
            fig = go.Figure(go.Bar(x=[0.10, cap10], y=["Random pick", "Our list"], orientation="h",
                                   marker=dict(color=[GRAY, P600], cornerradius=4), text=["10%", pct(cap10, 1)],
                                   textposition="outside", cliponaxis=False, hoverinfo="skip"))
            fig.update_xaxes(visible=False, range=[0, max(cap10, 0.1) * 1.3])
            fig.update_yaxes(showgrid=False)
            chart(style(fig, 140))
            st.markdown("<div class='ch-sub' style='margin-top:.6rem'><b style='color:#111827'>What the ranking looks at most</b></div>",
                        unsafe_allow_html=True)
            d = pd.DataFrame(e["drivers"]).head(6).iloc[::-1]
            fig = go.Figure(go.Bar(x=d.importance, y=d.label, orientation="h", marker=dict(color=P400, cornerradius=3),
                                   customdata=d.direction, hovertemplate="%{y}<br>%{customdata}<br>importance %{x:.3f}<extra></extra>"))
            fig.update_xaxes(visible=False)
            fig.update_yaxes(showgrid=False)
            chart(style(fig, 250))
            if lift < 1.5:
                st.caption("Harder to predict — treat this list as a helpful starting point, not a sure bet.")

    with card():
        card_head("Experiment log", "Kept only if it beats the current version in ≥90% of bootstrap resamples on the 30% test users")
        st.dataframe(log[["Event", "ID", "Change", "Best_model", "Test30_PR_AUC", "OOT_PR_AUC", "OOT_capture10", "Decision"]],
                     hide_index=True, width="stretch", column_config={
                         "Best_model": "Model", "Test30_PR_AUC": st.column_config.NumberColumn("Test PR-AUC", format="%.3f"),
                         "OOT_PR_AUC": st.column_config.NumberColumn("May PR-AUC", format="%.3f"),
                         "OOT_capture10": st.column_config.NumberColumn("May top-10% found", format="percent")})
        with st.expander("Technical details (for analysts)"):
            for name_, e in ev.items():
                o, v1 = e["oot"], e["v1_oot"]
                st.markdown(f"**{name_} — {e['version']} · {e['model']}**\n\n"
                            f"- Change vs {e['previous']}: {e['change']}\n"
                            f"- Out-of-time (May 2026): PR-AUC **{o['PR_AUC']:.3f}** (v1 {v1['PR_AUC']:.3f}, base rate {e['base_rate_oot']:.3f}); "
                            f"ROC-AUC {o['ROC_AUC']:.3f}; top-10% capture {pct(o['capture10'], 1)} (v1 {pct(v1['capture10'], 1)}); lift@10 {o['lift10']:.2f}×\n"
                            f"- 30% test users (Jan 2026): PR-AUC {e['test30']['PR_AUC']:.3f}; top-10% capture {pct(e['test30']['capture10'], 1)}\n"
                            f"- Live model trained on {e['live_train']['rows']:,} user-months ({e['live_train']['events']:,} events), "
                            f"snapshots {e['live_train']['snapshots']}")
