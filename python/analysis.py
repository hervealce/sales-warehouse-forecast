"""Build the star schema in DuckDB, then forecast weekly revenue (SARIMAX vs baselines)."""
import json, os, warnings, itertools
from pathlib import Path
import duckdb, numpy as np, pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
from style import style, BROWN, ACCENT

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]; os.chdir(ROOT); style(); FIG = ROOT / "figures"
con = duckdb.connect(str(ROOT / "data/warehouse.duckdb"))
def run(path):
    for s in path.read_text().split(";"):
        body = "\n".join(l for l in s.splitlines() if not l.strip().startswith("--")).strip()
        if not body: continue
        if body.upper().startswith("SELECT"): print(con.execute(body).df().to_string(index=False), "\n")
        else: con.execute(body)
run(ROOT / "sql/01_schema.sql"); run(ROOT / "sql/02_analysis.sql")

w = con.execute("SELECT week_start, revenue FROM weekly ORDER BY week_start").df().set_index("week_start")["revenue"]
w.index = pd.to_datetime(w.index); w = w.asfreq("W-MON").fillna(0)
w = w[(w.index > "2009-12-01") & (w.index < "2011-12-05")]       # drop partial first/last weeks
res = {"n_weeks": len(w), "adf_p_level": adfuller(w)[1], "adf_p_diff": adfuller(w.diff().dropna())[1]}

H = 13                                                            # hold out last quarter
train, test = w.iloc[:-H], w.iloc[-H:]
res["train_end"], res["test_range"] = str(train.index[-1].date()), [str(test.index[0].date()), str(test.index[-1].date())]
def score(pred): return dict(rmse=float(np.sqrt(mean_squared_error(test, pred))),
                             mape=float(100 * mean_absolute_percentage_error(test, pred)))
fc = {"naive_last_value": np.repeat(train.iloc[-1], H),
      "seasonal_naive_52wk": w.shift(52).iloc[-H:].values}
# growth-adjusted seasonal naive: last year's week x trailing 13-week YoY ratio
yoy = train.iloc[-13:].sum() / w.shift(52).loc[train.index[-13:]].sum()
res["trailing_yoy_ratio"] = float(yoy)
fc["seasonal_naive_x_yoy"] = w.shift(52).iloc[-H:].values * yoy
best = None
for p, d, q in itertools.product(range(3), [1], range(3)):
    try:
        m = SARIMAX(train, order=(p, d, q), seasonal_order=(0, 1, 0, 52)).fit(disp=False)
        if best is None or m.aic < best[1]: best = ((p, d, q), m.aic, m)
    except Exception: pass
res["sarima_order"] = f"SARIMA{best[0]}x(0,1,0,52)"; res["sarima_aic"] = best[1]
sar = best[2].get_forecast(H); fc["sarima"] = sar.predicted_mean.values
ci = sar.conf_int()
res["models"] = {k: score(v) for k, v in fc.items()}

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(w.index, w / 1e3, color=BROWN, lw=1.4, label="Actual")
ax.plot(test.index, fc["sarima"] / 1e3, color=ACCENT, lw=2, label=res["sarima_order"])
ax.fill_between(test.index, ci.iloc[:, 0] / 1e3, ci.iloc[:, 1] / 1e3, color=ACCENT, alpha=.2)
ax.plot(test.index, fc["seasonal_naive_52wk"] / 1e3, ls="--", color="#777", label="Same week last year")
ax.axvline(test.index[0], color="#aaa", ls=":")
ax.set(title="Weekly net revenue — 13-week holdout forecast", ylabel="Revenue (£ thousands)"); ax.legend()
fig.tight_layout(); fig.savefig(FIG / "forecast.png"); plt.close()

mods = res["models"]
fig, ax = plt.subplots(figsize=(7.5, 4))
names = list(mods); vals = [mods[n]["mape"] for n in names]
ax.barh(names, vals, color=["#b9a58f", BROWN, "#7d5a3c", ACCENT])
for i, v in enumerate(vals): ax.text(v + .5, i, f"{v:.1f}%", va="center")
ax.set(title="Forecast error on holdout (MAPE, lower is better)", xlabel="MAPE (%)")
fig.tight_layout(); fig.savefig(FIG / "model_mape.png"); plt.close()

c = con.execute("""SELECT c.country, sum(f.revenue) net FROM fact_sales f JOIN dim_customer c USING (customer_id)
                   GROUP BY 1 ORDER BY 2 DESC LIMIT 8""").df()
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(c.country[::-1], c.net[::-1] / 1e6, color=BROWN)
ax.set(title="Net revenue by customer country", xlabel="£ millions"); fig.tight_layout()
fig.savefig(FIG / "country_revenue.png"); plt.close()

(ROOT / "python/results.json").write_text(json.dumps(res, indent=2, default=float))
print(json.dumps(res, indent=2, default=float))
