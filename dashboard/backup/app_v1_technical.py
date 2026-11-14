"""Spin · Target-next-month dashboard (Team 5).

Run from the repository root:
    streamlit run dashboard/app.py
Data files are produced by Team5_Model_Experiments_v2.ipynb (dashboard/data/).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
st.set_page_config(page_title="Spin · Who to target next month", page_icon="🎯", layout="wide")

PERSONA_COLOR = {1: "#2a6fbb", 2: "#e0852b", 3: "#2f9e6e", 4: "#b0455f", 5: "#7b61c4", 6: "#8a8f98", 7: "#c2a52f"}
NO_PERSONA = "No persona (fewer than 3 active months)"
FEATURE_LABEL = {"oxxo_share": "Purchases at OXXO", "ecommerce_share": "Online purchases", "virtual_card_share": "Virtual-card use",
                 "intl_share": "International purchases", "cash_funding_share": "Cash top-ups", "spei_funding_share": "Bank-transfer top-ups",
                 "zero_funding_share": "Months spending without top-up", "monthly_spend": "Monthly spend", "active_months_share": "Months with purchases",
                 "decline_rate": "Declined payments"}
PERSONA_FEATS = list(FEATURE_LABEL)
CAMPAIGN = {"Flip-Out": dict(key="flip_out", what="flip-outs", label="Flip-Out · move spend outside OXXO",
                             offer="non-OXXO purchase incentive", event_desc="raise their share of purchases outside OXXO by 10+ points for two months in a row"),
            "Flip-In": dict(key="flip_in", what="flip-ins", label="Flip-In · win back cooled-down users",
                            offer="win-back incentive", event_desc="return to their usual number of card purchases (and at least 2 more than lately) for two months in a row")}


@st.cache_data
def load():
    card = json.loads((DATA / "model_card.json").read_text())
    live = pd.read_csv(DATA / "live_users.csv")
    bt = pd.read_csv(DATA / "backtest_may2026.csv")
    prof = pd.read_csv(DATA / "persona_profiles.csv")
    mon = pd.read_csv(DATA / "monthly.csv", parse_dates=["mes"])
    log = pd.read_csv(DATA / "experiment_log.csv")
    return card, live, bt, prof, mon, log


card, live, bt, prof, mon, log = load()
pname = dict(zip(prof.persona, prof.name))
pcolor_by_name = {pname[i]: PERSONA_COLOR[i] for i in pname} | {NO_PERSONA: "#c8ccd2"}


def low(label): return label.lower().replace("oxxo", "OXXO")


def pct(x, d=0): return f"{x * 100:.{d}f}%"
def month_name(s): return pd.Timestamp(s + "-01").strftime("%B %Y")


def fmt_value(feat, v):
    if feat == "monthly_spend": return f"${v:,.0f} MXN"
    return pct(v)


def profile_text(row, n=3):
    zs = {f: row[f"z_{f}"] for f in PERSONA_FEATS}
    top = sorted(zs, key=lambda f: -abs(zs[f]))[:n]
    return " · ".join(f"{'High' if zs[f] > 0 else 'Low'} {low(FEATURE_LABEL[f])} ({fmt_value(f, row[f'median_{f}'])})" for f in top)


def capture_curve(y, s):
    order = np.argsort(-s); y = np.asarray(y)[order]
    return np.arange(1, len(y) + 1) / len(y), np.cumsum(y) / max(y.sum(), 1)


# ---------------------------------------------------------------- sidebar
st.sidebar.title("🎯 Spin · Next-month targeting")
page = st.sidebar.radio("Section", ["Overview", "Personas", "Target list", "Model"], label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption(f"Data up to **{month_name(card['data_until'])}** · list built for the month after · "
                   f"generated {card['generated']}")
st.sidebar.caption("Flip-Out = a user moves purchases from OXXO to other merchants. "
                   "Flip-In = a user who slowed down comes back to using the card.")

st.info(f"**{card['decision']}**", icon="🧭")

# ---------------------------------------------------------------- OVERVIEW
if page == "Overview":
    st.title("Overview")
    last, first = mon.iloc[-1], mon.iloc[0]
    rated = mon.dropna(subset=["flip_out_rate"])
    lo, prev = rated.iloc[-1], rated.iloc[-2]
    n_out = int(live.flip_out_eligible.sum()); n_in = int(live.flip_in_eligible.sum())
    c = st.columns(5)
    c[0].metric("Active card users", f"{int(last.active_users):,}", f"{int(last.active_users - mon.iloc[-2].active_users):+,} vs previous month",
                help=f"Users with at least one approved purchase in {last.mes:%B %Y}.", border=True)
    c[1].metric("Purchases made at OXXO", pct(last.oxxo_share, 1), f"{(last.oxxo_share - mon.iloc[-2].oxxo_share) * 100:+.1f} pts vs previous month",
                delta_color="inverse", help="Share of all approved purchases that happened at OXXO.", border=True)
    c[2].metric("Flip-Out rate", pct(lo.flip_out_rate, 1), f"{(lo.flip_out_rate - prev.flip_out_rate) * 100:+.1f} pts",
                help=f"Share of eligible users who moved spend outside OXXO in the two months after {lo.mes:%B %Y} (latest month with known outcome).", border=True)
    c[3].metric("Flip-In rate", pct(lo.flip_in_rate, 1), f"{(lo.flip_in_rate - prev.flip_in_rate) * 100:+.1f} pts",
                help=f"Share of cooled-down users who came back to the card in the two months after {lo.mes:%B %Y}.", border=True)
    c[4].metric("Users we can target next month", f"{n_out:,}", f"+ {n_in:,} for win-back", delta_color="off",
                help="Flip-Out eligible: 3+ active months and 10%+ of purchases at OXXO. Win-back eligible: purchases slowed to ≤80% of usual.", border=True)

    left, right = st.columns([1.1, 1])
    with left:
        ps = prof.sort_values("users", ascending=True)
        big = prof.loc[prof.users.idxmax()]
        fig = px.bar(ps, x="users", y="name", orientation="h", color="name", color_discrete_map=pcolor_by_name,
                     text=[f"{u:,} · {pct(s)}" for u, s in zip(ps.users, ps.share_users)])
        fig.update_layout(title=f"{big['name']} are the largest group: {pct(big.share_users)} of users", showlegend=False,
                          xaxis_title="Users (latest month)", yaxis_title="", height=400, margin=dict(l=10, r=10, t=60, b=10))
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, width="stretch")
    with right:
        avg = (prof.flip_out_rate_may * prof.flip_out_eligible_live).sum() / prof.flip_out_eligible_live.sum()
        b = bt[bt.event == "Flip-Out"].groupby("persona_name").y.mean().reindex(prof.name).reset_index()
        b.columns = ["name", "rate"]; b = b.sort_values("rate")
        top, base = b.iloc[-1], bt[bt.event == "Flip-Out"].y.mean()
        fig = px.bar(b, x="rate", y="name", orientation="h", color="name", color_discrete_map=pcolor_by_name, text=[pct(r, 1) for r in b.rate])
        fig.add_vline(x=base, line_dash="dot", line_color="#555", annotation_text=f"all users {pct(base, 1)}", annotation_position="top")
        fig.update_layout(title=f"{top['name']} flip out {top.rate / base:.1f}× as often as the average user", showlegend=False,
                          xaxis_title="Flip-Out rate (users scored in May 2026, outcome June–July)", xaxis_tickformat=".0%", yaxis_title="",
                          height=400, margin=dict(l=10, r=10, t=60, b=10))
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, width="stretch")

    m = mon.copy()
    chg = (last.oxxo_share - first.oxxo_share) * 100
    fig = go.Figure()
    fig.add_scatter(x=m.mes, y=m.oxxo_share, mode="lines+markers", name="Purchases at OXXO", line=dict(color="#b0455f", width=3))
    fig.add_scatter(x=m.mes, y=m.flip_out_rate, mode="lines+markers", name="Flip-Out rate (by month scored)", line=dict(color="#2a6fbb", width=2, dash="dot"))
    fig.update_layout(title=f"OXXO's share of purchases {'rose' if chg > 0 else 'fell'} {abs(chg):.1f} pts between {first.mes:%b %Y} and {last.mes:%b %Y}",
                      yaxis_tickformat=".0%", yaxis_title="", xaxis_title="", height=360, legend=dict(orientation="h", y=-0.15), margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------- PERSONAS
elif page == "Personas":
    st.title("Personas")
    st.caption("Seven groups of users with similar habits: where they buy, how they load money, how much they spend. "
               "Sizes and profiles use the latest month; the Flip-Out / Flip-In rates are what actually happened to users scored in May 2026.")
    base_out = bt[bt.event == "Flip-Out"].y.mean(); base_in = bt[bt.event == "Flip-In"].y.mean()
    rows = [prof.iloc[i:i + 3] for i in range(0, len(prof), 3)]
    for chunk in rows:
        cols = st.columns(3)
        for col, (_, r) in zip(cols, chunk.iterrows()):
            with col.container(border=True):
                st.markdown(f"<div style='border-left:6px solid {PERSONA_COLOR[int(r.persona)]};padding-left:10px'>"
                            f"<b style='font-size:1.1rem'>P{int(r.persona)} · {r['name']}</b><br>"
                            f"<span style='color:#666'>{int(r.users):,} users ({pct(r.share_users)}) · {pct(r.share_spend)} of spend</span></div>",
                            unsafe_allow_html=True)
                st.markdown(f"**Profile:** {profile_text(r)}")
                a, b_ = st.columns(2)
                a.metric("Flip-Out rate", pct(r.flip_out_rate_may, 1), f"{r.flip_out_rate_may / base_out:.1f}× average", delta_color="off")
                b_.metric("Flip-In rate", pct(r.flip_in_rate_may, 1), f"{r.flip_in_rate_may / base_in:.1f}× average", delta_color="off")
                st.markdown(f"**Suggested action:** {r.action}")

    st.subheader("Compare personas")
    zc = [f"z_{f}" for f in PERSONA_FEATS]
    Z = prof.set_index("name")[zc]; Z.columns = [FEATURE_LABEL[f] for f in PERSONA_FEATS]
    M = prof.set_index("name")[[f"median_{f}" for f in PERSONA_FEATS]]
    txt = [[fmt_value(f, M.loc[n, f"median_{f}"]) for f in PERSONA_FEATS] for n in Z.index]
    top_ox = prof.loc[prof.z_oxxo_share.idxmax(), "name"]; top_on = prof.loc[prof.z_ecommerce_share.idxmax(), "name"]
    fig = go.Figure(go.Heatmap(z=Z.values, x=Z.columns, y=Z.index, text=txt, texttemplate="%{text}", colorscale="RdBu", reversescale=True,
                               zmid=0, zmin=-1.6, zmax=1.6, colorbar=dict(title="vs. average<br>(std. units)")))
    fig.update_layout(title=f"{top_ox} lean most on OXXO, while {top_on} buy most online",
                      height=430, margin=dict(l=10, r=10, t=60, b=10), xaxis_tickangle=-25)
    st.plotly_chart(fig, width="stretch")
    st.caption("Colour: red = above the average user, blue = below. Number = typical (median) value in the group.")

    pick = st.multiselect("Side-by-side: choose personas to compare", list(prof.name), default=[top_ox, top_on], max_selections=4)
    if pick:
        fig = go.Figure()
        cats = [FEATURE_LABEL[f] for f in PERSONA_FEATS]
        for n in pick:
            r = prof[prof.name == n].iloc[0]; vals = [float(np.clip(r[f"z_{f}"], -2, 2)) for f in PERSONA_FEATS]
            fig.add_scatterpolar(r=vals + vals[:1], theta=cats + cats[:1], name=n, line=dict(color=pcolor_by_name[n], width=2.5), fill="toself", opacity=.35)
        if len(pick) >= 2:
            d = (prof.set_index("name").loc[pick, zc].max() - prof.set_index("name").loc[pick, zc].min()).idxmax().replace("z_", "")
            title = f"These personas differ most on {low(FEATURE_LABEL[d])}"
        else:
            title = f"{pick[0]}: what sets them apart from the average user"
        fig.update_layout(title=title, polar=dict(radialaxis=dict(range=[-2, 2], tickvals=[-1, 0, 1], ticktext=["below avg", "average", "above avg"])),
                          height=520, legend=dict(orientation="h", y=-0.1), margin=dict(l=40, r=40, t=70, b=10))
        st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------- TARGET LIST
elif page == "Target list":
    st.title("Target list for next month")
    camp = st.segmented_control("Campaign", list(CAMPAIGN), default="Flip-Out", format_func=lambda k: CAMPAIGN[k]["label"]) or "Flip-Out"
    cfg = CAMPAIGN[camp]; k = cfg["key"]
    st.caption(f"Users ranked by how likely they are to {cfg['event_desc']}. Ranking uses each user's last 6 months up to "
               f"{month_name(card['live_month'])}; the list is for the following month.")

    pool = live[live[f"{k}_eligible"]].copy()
    pool["persona_name"] = pool.persona_name.fillna(NO_PERSONA)
    f1, f2, f3 = st.columns([2, 1.2, 1.2])
    personas = sorted(pool.persona_name.unique(), key=lambda n: (n == NO_PERSONA, n))
    sel_p = f1.multiselect("Persona", personas, default=personas)
    dec = f2.select_slider("Score decile (1 = most likely)", options=list(range(1, 11)), value=(1, 10))
    cap = f3.slider("Capacity: share of users to contact", 5, 30, 10, step=1, format="%d%%")

    flt = pool[pool.persona_name.isin(sel_p) & pool[f"{k}_decile"].between(*dec)].sort_values(f"{k}_score", ascending=False)
    n_contact = int(round(cap / 100 * len(flt)))

    b = bt[(bt.event == camp) & bt.persona_name.isin(sel_p) & bt.decile.between(*dec)]
    if len(b) and b.y.sum() > 0:
        x, cum = capture_curve(b.y.values, b.score.values)
        i = max(int(round(cap / 100 * len(b))) - 1, 0)
        caught, total = cum[i] * b.y.sum(), b.y.sum(); rand = cap / 100 * total
        m = st.columns(4)
        m[0].metric("Users to contact next month", f"{n_contact:,}", f"top {cap}% of {len(flt):,} eligible", delta_color="off", border=True)
        m[1].metric(f"{cfg['what'].capitalize()} caught (back-test)", f"{int(round(caught)):,} of {int(total):,}", f"{pct(cum[i])} of all {cfg['what']}",
                    delta_color="off", border=True, help="Same rule applied to users scored in May 2026, compared with what really happened in June–July 2026.")
        m[2].metric("With random selection", f"{int(round(rand)):,}", f"{pct(cap / 100)} of all {cfg['what']}", delta_color="off", border=True)
        m[3].metric("Gain vs random", f"{caught / rand:.2f}×", f"{int(round(caught - rand)):+,} extra {cfg['what']}", border=True)

        step = max(len(x) // 400, 1)
        fig = go.Figure()
        fig.add_scatter(x=x[::step], y=cum[::step], mode="lines", name="Ranked by our score", line=dict(color="#2a6fbb", width=3))
        fig.add_scatter(x=[0, 1], y=[0, 1], mode="lines", name="Random selection", line=dict(color="#8a8f98", dash="dot"))
        fig.add_scatter(x=[cap / 100], y=[cum[i]], mode="markers+text", marker=dict(size=12, color="#e0852b"), text=[f"  {pct(cum[i])} caught"],
                        textposition="middle right", name="Your capacity")
        fig.update_layout(title=f"Contacting the top {cap}% catches {pct(cum[i])} of {cfg['what']}: {caught / rand:.1f}× more than picking at random",
                          xaxis_title="Share of users contacted (highest score first)", yaxis_title=f"Share of all {cfg['what']} caught",
                          xaxis_tickformat=".0%", yaxis_tickformat=".0%", height=420, legend=dict(orientation="h", y=-0.2), margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, width="stretch")
    else:
        st.warning("No users match these filters in the back-test.")

    st.subheader(f"Who to contact: top {cap}% ({n_contact:,} users)")
    out = flt.head(n_contact).copy()
    out["Score"] = (out[f"{k}_score"] * 100).round(1)
    out["Rank"] = np.arange(1, len(out) + 1)
    show = out[["Rank", "userId", "persona_name", "Score", f"{k}_decile", "oxxo_share", "ecommerce_share", "monthly_spend", "tx_month_avg", "tx_last2_avg"]]
    show = show.rename(columns={"userId": "User ID", "persona_name": "Persona", f"{k}_decile": "Decile", "oxxo_share": "Purchases at OXXO",
                                "ecommerce_share": "Online purchases", "monthly_spend": "Monthly spend (MXN)", "tx_month_avg": "Usual purchases / month",
                                "tx_last2_avg": "Purchases / month, last 2"})
    smax = float(show.Score.max()) if len(show) else 100.0
    st.dataframe(show, hide_index=True, width="stretch", height=420, column_config={
        "Score": st.column_config.ProgressColumn("Likelihood score", help="Relative score (0–100). Higher = more likely. Use for ranking, not as an exact probability.",
                                                 min_value=0, max_value=smax, format="%.1f"),
        "Purchases at OXXO": st.column_config.NumberColumn(format="percent"), "Online purchases": st.column_config.NumberColumn(format="percent"),
        "Monthly spend (MXN)": st.column_config.NumberColumn(format="$%.0f"), "Usual purchases / month": st.column_config.NumberColumn(format="%.1f"),
        "Purchases / month, last 2": st.column_config.NumberColumn(format="%.1f")})
    mix = out.persona_name.value_counts(normalize=True)
    if len(mix):
        st.caption("List mix by persona: " + " · ".join(f"{n} {pct(v)}" for n, v in mix.items()))
    st.download_button("Download list (CSV)", show.to_csv(index=False).encode(), file_name=f"spin_{k}_targets_top{cap}pct.csv", mime="text/csv")
    st.caption("Keep a random 10% of this list uncontacted as a control group: it is the only way to measure what the campaign itself caused.")

# ---------------------------------------------------------------- MODEL
else:
    st.title("Model")
    tabs = st.tabs([CAMPAIGN[e]["label"] for e in card["events"]])
    for tab, (ev, e) in zip(tabs, card["events"].items()):
        with tab:
            what = CAMPAIGN[ev]["what"]
            st.markdown(f"**Current version:** {e['version']} · **Model:** {e['model']} · previous: {e['previous']}  \n"
                        f"**Live list trained on:** {e['live_train']['rows']:,} user-months ({e['live_train']['events']:,} {what}), snapshots {e['live_train']['snapshots']}")
            c = st.columns(4)
            o, v1 = e["oot"], e["v1_oot"]
            c[0].metric("Ranking quality (PR-AUC)", f"{o['PR_AUC']:.3f}", f"{o['PR_AUC'] - v1['PR_AUC']:+.3f} vs v1",
                        help=f"Out-of-time test (scored May 2026). Random ranking would score {e['base_rate_oot']:.3f} (the base rate).", border=True)
            c[1].metric("Caught in top 10%", pct(o["capture10"], 1), f"{(o['capture10'] - v1['capture10']) * 100:+.1f} pts vs v1",
                        help=f"Share of all {what} found by contacting the 10% highest-scored users. Random = 10%.", border=True)
            c[2].metric("Gain vs random in top 10%", f"{o['lift10']:.2f}×", border=True)
            c[3].metric("Check on 30% test users (Jan 2026)", f"PR-AUC {e['test30']['PR_AUC']:.3f}", f"top 10% catches {pct(e['test30']['capture10'], 1)}",
                        delta_color="off", border=True)

            d = pd.DataFrame(e["drivers"]).head(8)
            d["label_dir"] = d.label + "  (" + d.direction + ")"
            d = d.iloc[::-1]
            fig = px.bar(d, x="importance", y="label_dir", orientation="h", color_discrete_sequence=["#2a6fbb"])
            fig.update_layout(title=f"“{d.iloc[-1].label}” is the strongest signal for {what}", xaxis_title="How much ranking quality drops without it",
                              yaxis_title="", height=400, margin=dict(l=10, r=10, t=60, b=10))
            st.plotly_chart(fig, width="stretch")

            st.markdown("**What changed since the last version**")
            g = log[log.Event == ev]
            st.markdown(f"- Selected change: **{e['change']}**.\n"
                        f"- Out-of-time result: top 10% now catches **{pct(o['capture10'], 1)}** of {what} (v1: {pct(v1['capture10'], 1)}); "
                        f"PR-AUC {o['PR_AUC']:.3f} (v1: {v1['PR_AUC']:.3f}).\n"
                        f"- Experiments run this week: {len(g) - 1}; kept: {int(g.Decision.str.startswith('KEPT').sum())}.")
            if e["experiment"] == "E0":
                st.warning(f"No experiment beat last week's {ev} model by more than chance, so the v1 recipe is kept (retrained on the latest data).")
            tbl = g[["ID", "Change", "Reason", "Best_model", "Test30_PR_AUC", "Test30_capture10", "OOT_PR_AUC", "OOT_capture10", "Decision"]].rename(columns={
                "ID": "Exp.", "Best_model": "Model", "Test30_PR_AUC": "PR-AUC (30% test)", "Test30_capture10": "Top-10% catch (30% test)",
                "OOT_PR_AUC": "PR-AUC (May 2026)", "OOT_capture10": "Top-10% catch (May 2026)"})
            st.dataframe(tbl, hide_index=True, width="stretch", column_config={
                "PR-AUC (30% test)": st.column_config.NumberColumn(format="%.3f"), "PR-AUC (May 2026)": st.column_config.NumberColumn(format="%.3f"),
                "Top-10% catch (30% test)": st.column_config.NumberColumn(format="percent"), "Top-10% catch (May 2026)": st.column_config.NumberColumn(format="percent")})
            st.caption("Experiments are compared on the 30% test users. An experiment is kept only if it beats the current version in at least 90% of "
                       "bootstrap resamples, so the gain is bigger than chance. May 2026 is a final check that is never used to choose.")
