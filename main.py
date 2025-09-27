from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Any, Dict, List
from dotenv import load_dotenv

from .engine import run_recommendations
from .ml import train_elasticity_models
from .alerts import send_slack, send_email

load_dotenv()  

app = FastAPI(title="Smart Pricing Engine", version="0.1.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

@app.get("/health")
def health():
    return {"status": "ok"}

def to_native(x):
    try:
        import numpy as np, pandas as pd
        if isinstance(x, (np.floating,)): return float(x)
        if isinstance(x, (np.integer,)): return int(x)
        if pd.isna(x): return None
    except Exception:
        pass
    return x

@app.post("/recommend")
def recommend():
    """
    Build recommendations, send alerts for large changes, and return JSON.
    """
    try:
        # run engine (returns a DataFrame)
        recs_df = run_recommendations(DATA_DIR, save_csv=True)

        # make sure 'name' exists (nice for UI)
        if "name" not in recs_df.columns:
            recs_df["name"] = None

        # convert to pure JSON-safe rows
        rows: List[Dict[str, Any]] = []
        for _, r in recs_df.iterrows():
            rows.append({k: to_native(v) for k, v in r.items()})

        # ---- alerts (NOW inside the function, using local 'rows') ----
        changes = []
        for r in rows:
            try:
                pct_move = abs((r["recommended_price"] - r["current_price"]) / max(r["current_price"], 1e-6))
                big_delta = float(r.get("expected_profit_delta", 0)) >= 50.0   # tune threshold
                big_move  = pct_move >= 0.10                                   # ≥10% move
                if big_delta or big_move:
                    changes.append(r)
            except Exception:
                pass

        if changes:
            lines = [
                f'{c.get("name") or c["product_id"]}: ${to_native(c["current_price"]):.2f} → '
                f'${to_native(c["recommended_price"]):.2f} (Δprofit ${to_native(c["expected_profit_delta"]):.2f})'
                for c in changes[:20]
            ]
            text = "⚠️ Pricing Alerts\n" + "\n".join(lines)
            send_slack(text)
            send_email("Pricing Alerts", text)

        saved_path = str((DATA_DIR / "price_recommendations.csv").resolve())
        return {"message": "ok", "saved_csv_path": saved_path, "recommendations": rows}

    except Exception as e:
        import traceback; traceback.print_exc()
        return {"message": "error", "error": str(e)}

@app.post("/train")
def train():
    df = train_elasticity_models(DATA_DIR)
    return {"message": "ok", "trained": len(df), "scores": df.to_dict(orient="records")}