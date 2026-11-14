"""Build the baseline KPI files used by the dashboard.

Reads the Group 5 monthly panel and writes:
  data/kpi_monthly.csv   one row per month with the 4 KPI series
  data/kpi_baseline.json the fixed baseline window and its values

Run from the repository root (re-run whenever the panel is refreshed):
    python dashboard/build_kpis.py [path/to/g5_dataSample_v2_processed.csv]

KPI definitions (per ACTIVE user-month = at least 1 purchase in the month):
  ext_ratio        External spending ratio: mean over users of (1 - oxxo_tx_ratio_m), i.e. share of a
                   user's purchases made outside OXXO. Transaction-count based (the panel has no OXXO amount).
  tpv_mean/median  TPV per user: tx_amount_sum_m (MXN) per active user.
  mm_rate          Multi-merchant rate: share of active users with purchases at 2+ distinct merchants
                   (merchant_entropy_m > 0; entropy is 0 whenever a user has a single merchant).
  mm_activation    Multi-merchant activation: of users at 0-1 merchants in month M-1, share at 2+ merchants
                   in month M (labelled by the destination month M).
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
PANEL = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parents[1] / "EDAgroup5/data/g5_dataSample_v2_processed.csv"
BASELINE = ("2026-05", "2026-07")  # fixed baseline window (inclusive) — change deliberately, not on every refresh

g = pd.read_csv(PANEL, usecols=["userId", "mes", "oxxo_tx_ratio_m", "tx_count_m", "tx_amount_sum_m", "merchant_entropy_m"])
g["ym"] = pd.to_datetime(g.mes).dt.to_period("M")
g = g.sort_values(["userId", "ym"])
g["active"] = g.tx_count_m > 0
g["multi"] = g.active & (g.merchant_entropy_m > 0)

# activation transitions: M-1 at 0-1 merchants -> M at 2+ merchants (consecutive months only)
g["prev_multi"] = g.groupby("userId").multi.shift(1)
g["prev_ym"] = g.groupby("userId").ym.shift(1)
trans = g[(g.prev_ym == g.ym - 1) & (g.prev_multi == False)]  # noqa: E712

a = g[g.active].assign(ext=lambda d: 1 - d.oxxo_tx_ratio_m, ext_tx=lambda d: d.tx_count_m * (1 - d.oxxo_tx_ratio_m))


def kpis(act, tr):
    return dict(active_users=int(act.userId.nunique()), ext_ratio=act.ext.mean(),
                ext_ratio_portfolio=act.ext_tx.sum() / act.tx_count_m.sum(),
                tpv_mean=act.tx_amount_sum_m.mean(), tpv_median=act.tx_amount_sum_m.median(),
                mm_rate=act.multi.mean(), mm_activation=tr.multi.mean() if len(tr) else None,
                mm_pool=int(len(tr)))


monthly = pd.DataFrame([dict(mes=str(m), **kpis(a[a.ym == m], trans[trans.ym == m])) for m in sorted(a.ym.unique())])
monthly.loc[monthly.mm_pool == 0, "mm_activation"] = None
monthly.to_csv(HERE / "data/kpi_monthly.csv", index=False)

lo, hi = pd.Period(BASELINE[0]), pd.Period(BASELINE[1])
base = kpis(a[(a.ym >= lo) & (a.ym <= hi)], trans[(trans.ym >= lo) & (trans.ym <= hi)])
base.pop("active_users")
(HERE / "data/kpi_baseline.json").write_text(json.dumps(
    {"window": list(BASELINE), "source": PANEL.name, "values": base}, indent=1))
print(monthly.tail(4).round(3).to_string(index=False))
print("baseline", BASELINE, {k: round(v, 4) for k, v in base.items()})
