# Writes the CSVs the Power BI model loads, from Stats SA's official headline CPI:
#   data/forecasts.csv  every backtest forecast: made at the end of `origin`, for
#                       `target_month`, by one method, against the official rate
#   data/tests.csv      the Diebold-Mariano p-value per horizon (Ridge against no change)
#   data/calendar.csv   one row per month, with the inflation-targeting era marked
#   data/method.csv     the three forecasting methods
#   data/horizon.csv    the four horizons
#   data/expected.json  the error table the model's measures must reproduce
#
# The backtest is the one in statistical-modelling/cpi-inflation-forecast/cpi_forecast.py,
# with the same features, model, penalty and dates, so the errors match its published table.
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

DATA = Path(__file__).resolve().parent.parent / "data"
HORIZONS = [1, 3, 6, 12]
TRAIN_FROM = "2000-01"   # inflation targeting was adopted in February 2000
TEST_FROM = "2010-01"    # first forecast origin; every origin trains only on data before it
TARGETING_FROM = "2000-02"

METHODS = [
    ("Ridge on recent changes", "Ridge", 1),
    ("No change (last rate)", "No change", 2),
    ("Average of last 12 months", "12-month average", 3),
]


def load_cpi():
    cpi = pd.read_csv(DATA / "cpi_headline.csv", index_col="month", parse_dates=["month"])
    return cpi["yoy_rate_pct"], cpi["index_dec2024_100"]


def diebold_mariano(e_model, e_base, h):
    """Two-sided test that two forecasts have the same mean absolute error.
    Errors h months apart overlap, so the variance uses h - 1 autocovariances."""
    d = np.abs(e_model) - np.abs(e_base)
    n = len(d)
    d_c = d - d.mean()
    var = d_c @ d_c / n
    for k in range(1, h):
        var += 2 * (d_c[k:] @ d_c[:-k]) / n
    t = d.mean() / np.sqrt(var / n)
    return 2 * stats.t.sf(abs(t), df=n - 1)


def backtest(y, index):
    features = pd.DataFrame({
        "rate": y,
        "change_1m": y - y.shift(1),
        "change_3m": y - y.shift(3),
        "change_12m": y - y.shift(12),
        "momentum_3m": ((index / index.shift(3)) ** 4 - 1) * 100,
    })
    rows, tests = [], []
    for h in HORIZONS:
        target = y.shift(-h) - y
        data = features.assign(target=target).loc[TRAIN_FROM:].dropna(subset=features.columns)
        origins = data.loc[TEST_FROM:].dropna(subset=["target"]).index
        errors = {name: [] for name, _, _ in METHODS}
        for t in origins:
            train = data.loc[: t - pd.DateOffset(months=h)].dropna(subset=["target"])
            model = make_pipeline(StandardScaler(), Ridge(alpha=10.0))
            model.fit(train[features.columns], train["target"])
            actual = y[t + pd.DateOffset(months=h)]
            forecasts = {
                "Ridge on recent changes": y[t] + model.predict(data.loc[[t], features.columns])[0],
                "No change (last rate)": y[t],
                "Average of last 12 months": y.loc[t - pd.DateOffset(months=11): t].mean(),
            }
            for name, value in forecasts.items():
                errors[name].append(value - actual)
                rows.append({
                    "origin": t.strftime("%Y-%m-01"),
                    "target_month": (t + pd.DateOffset(months=h)).strftime("%Y-%m-01"),
                    "horizon": h,
                    "method": name,
                    "forecast": round(float(value), 4),
                    "actual": float(actual),
                })
        p = diebold_mariano(np.array(errors["Ridge on recent changes"]), np.array(errors["No change (last rate)"]), h)
        tests.append({"horizon": h, "p_ridge_vs_no_change": round(float(p), 4)})
    return pd.DataFrame(rows), pd.DataFrame(tests)


def calendar(y):
    months = pd.date_range(y.index.min(), y.index.max(), freq="MS")
    return pd.DataFrame({
        "month": months.strftime("%Y-%m-01"),
        "year": months.year,
        "month_no": months.month,
        "month_name": months.strftime("%b"),
        "year_month": months.strftime("%Y-%m"),
        "decade": (months.year // 10 * 10).astype(str) + "s",
        "era": np.where(months >= pd.Timestamp(TARGETING_FROM), "Inflation targeting", "Before inflation targeting"),
    })


def expected(forecasts, tests):
    mae = (forecasts.assign(abs_error=(forecasts["forecast"] - forecasts["actual"]).abs())
           .groupby(["horizon", "method"])["abs_error"].mean().round(3))
    return {
        "forecasts": int(len(forecasts)),
        "forecasts_per_horizon": {str(h): int(n) for h, n in forecasts.groupby("horizon").size().div(len(METHODS)).items()},
        "mae": {str(h): {m: float(mae[(h, m)]) for m, _, _ in METHODS} for h in HORIZONS},
        "p_ridge_vs_no_change": {str(r.horizon): r.p_ridge_vs_no_change for r in tests.itertuples()},
    }


def main():
    y, index = load_cpi()
    forecasts, tests = backtest(y, index)
    forecasts.to_csv(DATA / "forecasts.csv", index=False, lineterminator="\n")
    tests.to_csv(DATA / "tests.csv", index=False, lineterminator="\n")
    calendar(y).to_csv(DATA / "calendar.csv", index=False, lineterminator="\n")
    pd.DataFrame(METHODS, columns=["method", "short_name", "sort_order"]).to_csv(DATA / "method.csv", index=False, lineterminator="\n")
    pd.DataFrame({"horizon": HORIZONS, "horizon_label": [f"{h} month" + ("s" if h > 1 else "") + " ahead" for h in HORIZONS]}).to_csv(
        DATA / "horizon.csv", index=False, lineterminator="\n")
    (DATA / "expected.json").write_text(json.dumps(expected(forecasts, tests), indent=2) + "\n")
    print(f"Wrote {len(forecasts)} forecasts and {len(y)} months to data/")


if __name__ == "__main__":
    main()
