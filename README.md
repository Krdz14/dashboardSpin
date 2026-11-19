# dashboardSpin

Campaign dashboard for **Spin by OXXO** (Team 5). It answers one question: **who should we contact next month, and with which offer?**

The dashboard is a [Streamlit](https://streamlit.io) app that shows model results for two campaigns:

- **Flip-Out**: users likely to start buying more at stores other than OXXO for two months in a row. They are the audience for an offer to shop outside OXXO.
- **Flip-In**: users who had slowed down and are likely to return to their usual number of card purchases. They are the audience for a win-back offer.

## Pages

| Page | What it shows |
| --- | --- |
| **Overview** | Headline KPIs (active users, share of purchases at OXXO, Flip-Out and Flip-In audience sizes), plus baseline KPIs: external spending ratio, TPV per user and multi-merchant rate/activation. |
| **Customer groups** | 7 user segments with similar habits (where they shop, how they top up, how much they spend), with a suggested action for each. |
| **Who to contact** | Ranked list of users to target next month for each campaign, by model score. |
| **Model quality** | Backtest on May 2026, a month the model never saw in training: capture curves, lift and the experiment log. |

## Running it

**Requirements:** Python 3.10+

1. Install the dependencies (a virtual environment is recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r dashboard/requirements.txt
   ```

2. Start the app **from the repository root**, so the theme in `.streamlit/config.toml` is applied:

   ```bash
   streamlit run dashboard/app.py
   ```

3. Streamlit opens the dashboard in your browser, by default at <http://localhost:8501>.

All the data the app needs is already in `dashboard/data/`, so no extra setup is required.

## Refreshing the data

The files in `dashboard/data/` are generated outside this repo:

- `model_card.json`, `live_users.csv`, `backtest_may2026.csv`, `persona_profiles.csv`, `monthly.csv` and `experiment_log.csv` are exported by the `Team5_Model_Experiments_v2.ipynb` notebook.
- `kpi_monthly.csv` and `kpi_baseline.json` are built by `dashboard/build_kpis.py` from the Group 5 monthly panel:

  ```bash
  python dashboard/build_kpis.py path/to/g5_dataSample_v2_processed.csv
  ```

  If you leave out the path, the script looks for `../EDAgroup5/data/g5_dataSample_v2_processed.csv` next to this repo. The KPI baseline window (May–Jul 2026) is fixed in the script and only changes if you edit it.

## Project structure

```
dashboardSpin/
├── .streamlit/config.toml      # Spin theme (purple & white)
├── dashboard/
│   ├── app.py                  # Streamlit app (current version, v3)
│   ├── build_kpis.py           # builds the baseline KPI files
│   ├── requirements.txt
│   ├── assets/spin_logo.png
│   ├── data/                   # CSV/JSON inputs read by the app
│   └── backup/                 # earlier versions of the app (v1, v2)
└── design/                     # design references and mockups
```
