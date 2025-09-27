from pathlib import Path
import pandas as pd
import numpy as np

def load_all_csv(data_dir: Path):
    products = pd.read_csv(data_dir / "products.csv")
    sales = pd.read_csv(data_dir / "sales_history.csv")
    inventory = pd.read_csv(data_dir / "inventory.csv")
    competitors = pd.read_csv(data_dir / "competitors.csv")

    sales["date"] = pd.to_datetime(sales["date"])
    sales["promo_flag"] = sales["promo_flag"].astype(int)
    sales["dow"] = sales["date"].dt.dayofweek
    sales["is_weekend"] = (sales["dow"].isin([5, 6])).astype(int)
    return products, sales, inventory, competitors

def recent_competitor_price(competitors, sales, pid, window_days=7):
    df = competitors[competitors["product_id"] == pid].copy()
    if df.empty:
        return np.nan
    ref_date = sales["date"].max()
    cutoff = ref_date - pd.Timedelta(days=window_days)
    df["date"] = pd.to_datetime(df["date"])
    recent = df[df["date"].between(cutoff, ref_date)]
    if recent.empty:
        return df["competitor_price"].median()
    return recent["competitor_price"].median()

def fit_simple_model(sdf):
    X = np.c_[
        np.ones(len(sdf)),
        sdf["price_at_sale"].values,
        sdf["is_weekend"].values,
        sdf["promo_flag"].values
    ]
    y = sdf["units_sold"].values.astype(float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta

def predict_units(beta, price, weekend_prob=2/7, promo=0):
    b0, bp, bw, bpr = beta
    weekday_units = b0 + bp*price
    weekend_units = b0 + bp*price + bw
    expected = (1-weekend_prob)*weekday_units + weekend_prob*weekend_units
    return max(0.0, expected)

def candidate_prices(cost, current, comp_median):
    lo = max(cost * 1.10, current * 0.70)
    hi = current * 1.30
    if not np.isnan(comp_median):
        lo = max(lo, comp_median * 0.85)
        hi = min(hi, comp_median * 1.15)
    if hi <= lo:
        hi = lo * 1.05
    return np.round(np.linspace(lo, hi, num=25), 2)