"""Spin · Who to contact next month (Team 5) — simplified, plain-language dashboard.

Run from the repository root:
    streamlit run dashboard/app.py
Data files are produced by Team5_Model_Experiments_v2.ipynb (dashboard/data/).
The previous, more technical version is kept in dashboard/backup/app_v1_technical.py.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
st.set_page_config(page_title="Spin · Who to contact next month", page_icon="🎯", layout="wide")

# ---------------------------------------------------------------- look & feel
ACCENT, MUTED, SOFT, INK, SUB = "#2a6fbb", "#c9ced6", "#eef3fa", "#1f2937", "#6b7280"
GOOD, WARN = "#2f9e6e", "#c27c1a"

st.markdown(f"""
<style>
  .block-container {{max-width: 1100px; padding-top: 2rem; padding-bottom: 4rem;}}
  h1 {{font-weight: 700; letter-spacing: -0.5px;}}
  h3 {{margin-top: 1.6rem;}}
  [data-testid="stMetricValue"] {{font-size: 2rem;}}
  [data-testid="stMetricLabel"] p {{font-size: 0.95rem; color: {SUB};}}
  .lead {{font-size: 1.15rem; color: {SUB}; margin: -0.4rem 0 1.4rem 0; line-height: 1.5;}}
  .card {{background: {SOFT}; border-radius: 14px; padding: 1.1rem 1.3rem; margin-bottom: 0.8rem; line-height: 1.6;}}
  .card b {{color: {INK};}}
  .big {{font-size: 1.25rem; line-height: 1.6;}}
  .pill {{display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.85rem; margin: 2px 4px 2px 0;
          background: #fff; border: 1px solid {MUTED}; color: {INK};}}
  .hi {{background: #e6f4ee; border-color: #b5dcc8; color: #1d6b49;}}
  .lo {{background: #fbf0e6; border-color: #ecc9a3; color: #8a5414;}}
  .muted {{color: {SUB}; font-size: 0.92rem;}}
</style>
""", unsafe_allow_html=True)


def lead(text): st.markdown(f"<div class='lead'>{text}</div>", unsafe_allow_html=True)
def card(html): st.markdown(f"<div class='card'>{html}</div>", unsafe_allow_html=True)
def pct(x, d=0): return f"{x * 100:.{d}f}%"
def month_name(s): return pd.Timestamp(s + "-01").strftime("%B %Y")


def clean(fig, h=340):
    """One calm chart style for the whole app."""
    fig.update_layout(template="plotly_white", height=h, showlegend=False, margin=dict(l=10, r=30, t=50, b=10),
                      font=dict(size=14, color=INK), title_font=dict(size=17), hoverlabel=dict(bgcolor="white"))
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


# ---------------------------------------------------------------- plain-language vocabulary
CAMPAIGN = {
    "Flip-Out": dict(key="flip_out", short="Move spend outside OXXO", people="users who move their spending outside OXXO",
                     icon="🛒", offer="an offer to shop outside OXXO",
                     meaning="Users who start buying more at other stores (not OXXO) for two months in a row."),
    "Flip-In": dict(key="flip_in", short="Win back quiet users", people="quiet users who come back to the card",
                    icon="🔁", offer="a win-back offer",
                    meaning="Users who had slowed down and go back to their usual number of card purchases for two months in a row."),
}
# What each habit means in everyday words when a group is clearly above / below the average user.
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
HABIT = {"oxxo_share": "Shops at OXXO", "ecommerce_share": "Buys online", "virtual_card_share": "Virtual card",
         "intl_share": "International", "cash_funding_share": "Cash top-ups", "spei_funding_share": "Bank transfers",
         "zero_funding_share": "Spends w/o top-up", "monthly_spend": "Monthly spend", "active_months_share": "Active months",
         "decline_rate": "Declined payments"}


def traits(row, n=3):
    z = {f: row[f"z_{f}"] for f in TRAIT}
    top = [f for f in sorted(z, key=lambda f: -abs(z[f])) if abs(z[f]) >= 0.3][:n]
    return [(TRAIT[f][0] if z[f] > 0 else TRAIT[f][1], z[f] > 0) for f in top]


def level(ratio):
    if ratio >= 1.1: return "Higher than average", "hi"
    if ratio <= 0.9: return "Lower than average", "lo"
    return "About average", ""


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
    return card_, live_, bt_, prof_, mon_, log_


mc, live, bt, prof, mon, log = load()
NO_GROUP = "No group yet (new user)"
avg_rate = {ev: bt[bt.event == ev].y.mean() for ev in CAMPAIGN}

# ---------------------------------------------------------------- sidebar
PAGES = {"🏠  Summary": "summary", "👥  Customer groups": "groups", "📋  Who to contact": "list", "✅  Can we trust it?": "trust"}
st.sidebar.markdown("## 🎯 Spin")
st.sidebar.markdown("**Who to contact next month**")
page = PAGES[st.sidebar.radio("Go to", list(PAGES), label_visibility="collapsed")]
st.sidebar.divider()
st.sidebar.markdown(
    f"<div class='muted'>Data up to <b>{month_name(mc['data_until'])}</b>.<br>Updated {mc['generated']}.<br><br>"
    "<b>🛒 Move spend outside OXXO</b><br>" + CAMPAIGN["Flip-Out"]["meaning"] + "<br><br>"
    "<b>🔁 Win back quiet users</b><br>" + CAMPAIGN["Flip-In"]["meaning"] + "</div>", unsafe_allow_html=True)

# ================================================================ SUMMARY
if page == "summary":
    st.title("Summary")
    lead("Who should Spin contact next month, and why. Three numbers and the key takeaways.")

    last, prev = mon.iloc[-1], mon.iloc[-2]
    n_out, n_in = int(live.flip_out_eligible.sum()), int(live.flip_in_eligible.sum())
    c = st.columns(3)
    c[0].metric("People using the card", f"{int(last.active_users):,}", f"{int(last.active_users - prev.active_users):+,} vs last month",
                border=True, help=f"Users with at least one purchase in {last.mes:%B %Y}.")
    c[1].metric("🛒 Could shop outside OXXO", f"{n_out:,}", "users we can contact", delta_color="off", border=True,
                help="Users who still do a good part of their shopping at OXXO.")
    c[2].metric("🔁 Could be won back", f"{n_in:,}", "users we can contact", delta_color="off", border=True,
                help="Users who are using the card less than they usually do.")

    st.subheader("Key takeaways")
    big = prof.loc[prof.users.idxmax()]
    rates = bt[bt.event == "Flip-Out"].groupby("persona_name").y.mean()
    top_g = rates.idxmax()
    rated = mon.dropna(subset=["flip_out_rate"])
    f0, f1 = rated.iloc[0], rated.iloc[-1]
    ox0, ox1 = mon.iloc[0].oxxo_share, last.oxxo_share
    lift = mc["events"]["Flip-Out"]["oot"]["lift10"]
    card(f"<div class='big'>"
         f"1. The biggest group is <b>{big['name']}</b>: about {pct(big.share_users)} of all users.<br>"
         f"2. <b>{top_g}</b> are the most likely to start shopping outside OXXO "
         f"({rates.max() / avg_rate['Flip-Out']:.1f}× the average user).<br>"
         f"3. Fewer people are moving spend outside OXXO on their own: from {pct(f0.flip_out_rate)} in {f0.mes:%b %Y} "
         f"to {pct(f1.flip_out_rate)} in {f1.mes:%b %Y}. That is why a campaign is useful now.<br>"
         f"4. Our list finds the right people <b>{lift:.1f}× better than picking at random</b>.</div>")

    st.subheader("Which groups are most likely to shop outside OXXO?")
    b = rates.reindex(prof.name).rename("rate").reset_index().rename(columns={"persona_name": "name"}).sort_values("rate")
    colors = [ACCENT if r >= b.rate.nlargest(2).min() else MUTED for r in b.rate]
    fig = go.Figure(go.Bar(x=b.rate, y=b.name, orientation="h", marker_color=colors, text=[pct(r) for r in b.rate],
                           textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x:.0%}<extra></extra>"))
    fig.add_vline(x=avg_rate["Flip-Out"], line_dash="dot", line_color=SUB,
                  annotation_text=f"average {pct(avg_rate['Flip-Out'])}", annotation_position="top")
    fig.update_xaxes(visible=False)
    st.plotly_chart(clean(fig, 360), width="stretch")
    st.caption("Share of each group that actually moved spend outside OXXO in June–July 2026. Blue = the two best groups to target.")

    with st.expander("See how OXXO use has changed month by month"):
        fig = go.Figure(go.Scatter(x=mon.mes, y=mon.oxxo_share, mode="lines+markers", line=dict(color=ACCENT, width=3),
                                   hovertemplate="%{x|%b %Y}: %{y:.1%}<extra></extra>"))
        fig.update_layout(title=f"Share of purchases made at OXXO: {pct(ox0, 1)} → {pct(ox1, 1)}")
        fig.update_yaxes(tickformat=".0%", showgrid=True, gridcolor="#f0f0f0")
        st.plotly_chart(clean(fig, 300), width="stretch")

# ================================================================ CUSTOMER GROUPS
elif page == "groups":
    st.title("Customer groups")
    lead("We sorted users into 7 groups with similar habits (where they shop, how they load money, how much they spend). "
         "Pick a group to see who they are and what to offer them.")

    order = prof.sort_values("users", ascending=False)
    name = st.pills("Group", list(order.name), default=order.name.iloc[0], label_visibility="collapsed") or order.name.iloc[0]
    r = prof[prof.name == name].iloc[0]

    left, right = st.columns([1.3, 1], gap="large")
    with left:
        chips = "".join(f"<span class='pill {'hi' if up else 'lo'}'>{t}</span>" for t, up in traits(r))
        card(f"<div style='font-size:1.4rem;font-weight:700;margin-bottom:.3rem'>{name}</div>"
             f"<div class='muted'>{int(r.users):,} users · {pct(r.share_users)} of all users · {pct(r.share_spend)} of total spend</div>"
             f"<div style='margin-top:.8rem'>{chips}</div>")
        st.markdown("**💡 What to offer them**")
        st.markdown(r.action)
    with right:
        for ev, col in (("Flip-Out", "flip_out_rate_may"), ("Flip-In", "flip_in_rate_may")):
            txt, cls = level(r[col] / avg_rate[ev])
            card(f"{CAMPAIGN[ev]['icon']} <b>{CAMPAIGN[ev]['short']}</b><br>"
                 f"<span class='pill {cls}'>{txt}</span> <span class='muted'>{pct(r[col])} vs {pct(avg_rate[ev])} average</span>")

    st.subheader("All groups at a glance")
    tbl = order.assign(
        Users=order.users,
        **{"Share of users": order.share_users},
        **{"🛒 Outside OXXO": [level(x / avg_rate["Flip-Out"])[0] for x in order.flip_out_rate_may]},
        **{"🔁 Win back": [level(x / avg_rate["Flip-In"])[0] for x in order.flip_in_rate_may]},
        **{"What defines them": [" · ".join(t for t, _ in traits(row, 2)) for _, row in order.iterrows()]},
    ).rename(columns={"name": "Group"})[["Group", "Users", "Share of users", "What defines them", "🛒 Outside OXXO", "🔁 Win back"]]
    st.dataframe(tbl, hide_index=True, width="stretch", column_config={
        "Share of users": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=float(order.share_users.max())),
        "Users": st.column_config.NumberColumn(format="%d")})

    with st.expander("Detailed comparison of habits (for analysts)"):
        Z = prof.set_index("name")[[f"z_{f}" for f in TRAIT]].clip(-1.5, 1.5)
        Z.columns = [HABIT[f] for f in TRAIT]
        fig = go.Figure(go.Heatmap(z=Z.values, x=Z.columns, y=Z.index, zmid=0, showscale=False,
                                   colorscale=[[0, "#e8a463"], [0.5, "#ffffff"], [1, "#4f8fd1"]],
                                   hovertemplate="%{y}<br>%{x}<extra></extra>", xgap=3, ygap=3))
        fig.update_xaxes(side="top")
        st.plotly_chart(clean(fig, 380), width="stretch")
        st.caption("Blue = this group does it more than the average user. Orange = less. White = about average.")

# ================================================================ WHO TO CONTACT
elif page == "list":
    st.title("Who to contact")
    lead(f"A ranked list for next month, based on data up to {month_name(mc['live_month'])}. "
         "Choose a campaign and how many people you can reach — the most likely people come first.")

    camp = st.segmented_control("1 · Choose a campaign", list(CAMPAIGN), default="Flip-Out",
                                format_func=lambda k: f"{CAMPAIGN[k]['icon']}  {CAMPAIGN[k]['short']}") or "Flip-Out"
    cfg = CAMPAIGN[camp]; k = cfg["key"]
    st.caption(cfg["meaning"])

    pool = live[live[f"{k}_eligible"]].copy()
    pool["persona_name"] = pool.persona_name.fillna(NO_GROUP)
    cap = st.slider("2 · What share of these users can you contact?", 5, 30, 10, step=5, format="%d%%",
                    help=f"There are {len(pool):,} users who could receive {cfg['offer']}.")

    with st.expander("Filter by customer group (optional)"):
        groups = sorted(pool.persona_name.unique(), key=lambda n: (n == NO_GROUP, n))
        sel = st.multiselect("Customer groups", groups, default=groups, label_visibility="collapsed")

    flt = pool[pool.persona_name.isin(sel)].sort_values(f"{k}_score", ascending=False)
    n_contact = int(round(cap / 100 * len(flt)))

    b = bt[(bt.event == camp) & bt.persona_name.isin(sel)]
    if len(b) and b.y.sum() > 0 and n_contact > 0:
        x, cum = capture_curve(b.y.values, b.score.values)
        i = max(int(round(cap / 100 * len(b))) - 1, 0)
        gain = cum[i] / (cap / 100)
        card(f"<div class='big'>Contact <b>{n_contact:,} users</b> (the top {cap}%).<br>"
             f"When we tested this on past data, that list reached <b>{pct(cum[i])}</b> of all {cfg['people']} — "
             f"<b>{gain:.1f}× more</b> than picking {cap}% of users at random.</div>")

        with st.expander("How did we estimate this?"):
            st.markdown("We scored users as of May 2026, then checked who really changed in June–July 2026. "
                        "The blue line shows how many of them we would have found by contacting more and more of the list.")
            step = max(len(x) // 300, 1)
            fig = go.Figure()
            fig.add_scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(color=MUTED, dash="dot"), hoverinfo="skip")
            fig.add_scatter(x=x[::step], y=cum[::step], mode="lines", line=dict(color=ACCENT, width=3),
                            hovertemplate="Contact %{x:.0%} → find %{y:.0%}<extra></extra>")
            fig.add_scatter(x=[cap / 100], y=[cum[i]], mode="markers", marker=dict(size=12, color=WARN), hoverinfo="skip")
            fig.add_annotation(x=0.75, y=0.62, text="random picking", showarrow=False, font=dict(color=SUB))
            fig.update_xaxes(title="Share of users contacted", tickformat=".0%")
            fig.update_yaxes(title="Share of the right people found", tickformat=".0%", showgrid=True, gridcolor="#f0f0f0")
            st.plotly_chart(clean(fig, 340), width="stretch")
    elif not sel:
        st.warning("Pick at least one customer group.")

    st.subheader(f"The list · {n_contact:,} users")
    out = flt.head(n_contact).copy()
    out["Priority"] = pd.cut(np.arange(len(out)) / max(len(out), 1), [-1, 1 / 3, 2 / 3, 2],
                             labels=["⭐⭐⭐ Highest", "⭐⭐ High", "⭐ Good"]).astype(str)
    show = out.rename(columns={"userId": "User ID", "persona_name": "Customer group", "oxxo_share": "Purchases at OXXO",
                               "ecommerce_share": "Online purchases", "monthly_spend": "Monthly spend (MXN)"})
    show.insert(0, "#", np.arange(1, len(show) + 1))
    base_cols = ["#", "User ID", "Priority", "Customer group"]
    more = st.toggle("Show spending details", value=False)
    cols = base_cols + (["Purchases at OXXO", "Online purchases", "Monthly spend (MXN)"] if more else [])
    st.dataframe(show[cols], hide_index=True, width="stretch", height=400, column_config={
        "Purchases at OXXO": st.column_config.NumberColumn(format="percent"),
        "Online purchases": st.column_config.NumberColumn(format="percent"),
        "Monthly spend (MXN)": st.column_config.NumberColumn(format="$%.0f")})

    d1, d2 = st.columns([1, 2.2])
    d1.download_button("⬇️  Download list (CSV)", show[base_cols + ["Purchases at OXXO", "Online purchases", "Monthly spend (MXN)"]]
                       .to_csv(index=False).encode(), file_name=f"spin_{k}_top{cap}pct.csv", mime="text/csv", width="stretch")
    d2.caption("Tip: leave a random 10% of this list without the offer. Comparing both groups afterwards shows "
               "how much the campaign really helped.")

# ================================================================ CAN WE TRUST IT?
else:
    st.title("Can we trust the list?")
    lead("We tested the ranking on months it had never seen. Here is how much better it is than picking users at random.")

    cols = st.columns(2, gap="large")
    for col, (ev, e) in zip(cols, mc["events"].items()):
        cfg, lift, cap10 = CAMPAIGN[ev], e["oot"]["lift10"], e["oot"]["capture10"]
        verdict, color = (("Strong", GOOD) if lift >= 2 else ("Useful", ACCENT) if lift >= 1.5 else ("Weak · use with care", WARN))
        with col:
            st.markdown(f"### {cfg['icon']} {cfg['short']}")
            st.markdown(f"<span class='pill' style='border-color:{color};color:{color};font-weight:600'>{verdict}</span>",
                        unsafe_allow_html=True)
            fig = go.Figure(go.Bar(x=[cap10, 0.10], y=["Our list", "Random pick"], orientation="h", marker_color=[color, MUTED],
                                   text=[pct(cap10), "10%"], textposition="outside", cliponaxis=False, hoverinfo="skip"))
            fig.update_layout(title=dict(text="Found by contacting 10% of users", font=dict(size=14)))
            fig.update_xaxes(visible=False, range=[0, max(cap10, 0.1) * 1.3])
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(clean(fig, 200), width="stretch")
            st.markdown(f"Contacting the top 10% of the list finds **{pct(cap10)}** of the {cfg['people']} — "
                        f"**{lift:.1f}×** what random picking finds.")
            st.markdown("**What the ranking looks at most:**")
            st.markdown("\n".join(f"- {d['label']}" for d in e["drivers"][:3]))
            if lift < 1.5:
                st.info("This one is harder to predict. Treat the list as a helpful starting point, not a sure bet.", icon="ℹ️")

    with st.expander("Technical details (for analysts)"):
        for ev, e in mc["events"].items():
            st.markdown(f"#### {ev} — {e['version']} · {e['model']}")
            o, v1 = e["oot"], e["v1_oot"]
            st.markdown(f"- Change vs {e['previous']}: {e['change']}\n"
                        f"- Out-of-time (May 2026): PR-AUC **{o['PR_AUC']:.3f}** (v1 {v1['PR_AUC']:.3f}, base rate {e['base_rate_oot']:.3f}); "
                        f"ROC-AUC {o['ROC_AUC']:.3f}; top-10% capture {pct(o['capture10'], 1)} (v1 {pct(v1['capture10'], 1)}); lift@10 {o['lift10']:.2f}×\n"
                        f"- 30% test users (Jan 2026): PR-AUC {e['test30']['PR_AUC']:.3f}; top-10% capture {pct(e['test30']['capture10'], 1)}\n"
                        f"- Live model trained on {e['live_train']['rows']:,} user-months ({e['live_train']['events']:,} events), "
                        f"snapshots {e['live_train']['snapshots']}")
            d = pd.DataFrame(e["drivers"]).head(8).iloc[::-1]
            fig = px.bar(d, x="importance", y=d.label + "  (" + d.direction + ")", orientation="h", color_discrete_sequence=[ACCENT])
            fig.update_layout(title="Permutation importance (drop in PR-AUC)", yaxis_title="", xaxis_title="")
            st.plotly_chart(clean(fig, 320), width="stretch")
        st.markdown("#### Experiment log")
        st.dataframe(log[["Event", "ID", "Change", "Best_model", "Test30_PR_AUC", "OOT_PR_AUC", "OOT_capture10", "Decision"]],
                     hide_index=True, width="stretch", column_config={
                         "Test30_PR_AUC": st.column_config.NumberColumn(format="%.3f"),
                         "OOT_PR_AUC": st.column_config.NumberColumn(format="%.3f"),
                         "OOT_capture10": st.column_config.NumberColumn(format="percent")})
        st.caption("An experiment is kept only if it beats the current version in ≥90% of bootstrap resamples on the 30% test users. "
                   "May 2026 is a final check never used for selection.")
