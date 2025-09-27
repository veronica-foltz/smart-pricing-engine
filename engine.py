from pathlib import Path
import pandas as pd
import numpy as np
from .utils import (
    load_all_csv,
    recent_competitor_price,
    fit_simple_model,
    predict_units,
    candidate_prices,
)
from .ml import predict_units_ml

def run_recommendations(data_dir: Path, save_csv: bool = True):
    products, sales, inventory, competitors = load_all_csv(data_dir)
    rows = []

    # defensive: ensure required columns exist
    for df_name, df, cols in [
        ("products", products, ["product_id","unit_cost","current_price"]),
        ("sales", sales, ["date","product_id","units_sold","price_at_sale","promo_flag","is_weekend"]),
        ("inventory", inventory, ["product_id","on_hand","reorder_point"]),
    ]:
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"{df_name} is missing columns: {missing}")

    ref_date = sales["date"].max()

    prod_ids = set(products["product_id"])
    inv_index = {row["product_id"]: row for _, row in inventory.iterrows()}

    for _, prod in products.iterrows():
        pid = str(prod["product_id"])
        cost = float(prod["unit_cost"])
        current = float(prod["current_price"])

        sdf = sales[sales["product_id"] == pid].copy()

        # if no sales, keep current price
        if len(sdf) < 5:
            rows.append({
                "product_id": pid,
                "current_price": current,
                "recommended_price": current,
                "unit_cost": cost,
                "competitor_median_price": None,
                "inventory_on_hand": int(inv_index.get(pid, {}).get("on_hand", 0)) if isinstance(inv_index.get(pid, {}), dict) else int(inv_index.get(pid, pd.Series({"on_hand":0}))["on_hand"]),
                "reorder_point": int(inv_index.get(pid, {}).get("reorder_point", 0)) if isinstance(inv_index.get(pid, {}), dict) else int(inv_index.get(pid, pd.Series({"reorder_point":0}))["reorder_point"]),
                "expected_profit_delta": 0.0,
                "notes": "Not enough sales history; keep current price."
            })
            continue

        # fit tiny model
        beta = fit_simple_model(sdf)

        # competitor median
        comp_med = recent_competitor_price(competitors, sales, pid, 7)

        # inventory (handle missing row)
        inv_row = inv_index.get(pid)
        if inv_row is None or (isinstance(inv_row, float) and pd.isna(inv_row)):
            on_hand = 0
            rpoint = 0
        else:
            # inv_row may be a Series
            on_hand = int(inv_row["on_hand"])
            rpoint = int(inv_row["reorder_point"])

        # build candidate price band
        cands = candidate_prices(cost, current, comp_med)

        # profit = units * (price - cost)
        profits = []
        for p in cands:
            u = predict_units(beta, p)
            profits.append(u * (p - cost))
        profits = np.array(profits)
        idx = int(np.argmax(profits))
        base_rec = float(cands[idx])
        base_profit = float(profits[idx])

        # inventory nudges
        rec = base_rec
        notes = []
        if on_hand <= rpoint:
            rec = round(rec * 1.03, 2)
            notes.append("Low inventory → +3% price.")
        elif on_hand > 2 * rpoint:
            rec = round(rec * 0.97, 2)
            notes.append("High inventory → -3% price.")

        # clamp to candidate band
        rec = float(np.clip(rec, cands.min(), cands.max()))

        # inside loop where you evaluate candidate prices:
        use_ml = predict_units_ml(pid, price=0) is not None
        def units(price):
            ml = predict_units_ml(pid, price)
            return ml if (ml is not None) else predict_units(beta, price)

        profits, points = [], []
        for p in cands:
            u = units(p)
            profits.append(u * (p - cost))

        # expected improvement vs current
        base_units = predict_units(beta, current)
        base_profit_current = base_units * (current - cost)
        expected_delta = round(base_profit - base_profit_current, 2)

        if pd.isna(comp_med):
            notes.append("No recent competitor price; used safety band.")
        else:
            notes.append(f"Competitor median ≈ {float(comp_med):.2f} (±15% band).")

        rows.append({
            "product_id": pid,
            "current_price": current,
            "recommended_price": rec,
            "unit_cost": cost,
            "competitor_median_price": None if pd.isna(comp_med) else float(comp_med),
            "inventory_on_hand": on_hand,
            "reorder_point": rpoint,
            "expected_profit_delta": expected_delta,
            "notes": " ".join(notes) if notes else "Maximized expected profit under guardrails."
        })

    recs = pd.DataFrame(rows).sort_values("expected_profit_delta", ascending=False)
    
    from pathlib import Path
    prods_df = pd.read_csv(Path(data_dir) / "products.csv")
    if  "name" in prods_df.columns:
        recs = recs.merge(prods_df[["product_id", "name"]], on="product_id", how="left")
    else:
        recs["name"] = None

    if save_csv:
        out = data_dir / "price_recommendations.csv"
        recs.to_csv(out, index=False)

    return recs