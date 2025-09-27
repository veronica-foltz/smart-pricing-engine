from pathlib import Path
import pandas as pd, numpy as np, joblib
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

def _elasticity_at(beta_price, price, q):
    # elasticity = (dQ/dP) * (P/Q)
    if q <= 0: return 0.0
    return float(beta_price * price / q)

def train_elasticity_models(data_dir: Path):
    sales = pd.read_csv(data_dir / "sales_history.csv", parse_dates=["date"])
    sales["dow"] = sales["date"].dt.dayofweek
    sales["is_weekend"] = (sales["dow"].isin([5,6])).astype(int)
    X_cols = ["price_at_sale", "is_weekend", "promo_flag"]
    results = []
    for pid, sdf in sales.groupby("product_id"):
        if len(sdf) < 30: continue
        X = sdf[X_cols].astype(float).values
        y = sdf["units_sold"].astype(float).values
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        model = Ridge(alpha=1.0).fit(X_tr, y_tr)
        joblib.dump(model, MODELS_DIR / f"{pid}.joblib")
        results.append({"product_id": pid, "r2": float(model.score(X_te, y_te))})
    return pd.DataFrame(results)

def predict_units_ml(pid: str, price: float, weekend_prob=2/7, promo=0):
    path = MODELS_DIR / f"{pid}.joblib"
    if not path.exists(): return None  # fallback to rules engine
    model = joblib.load(path)
    x_weekday = np.array([[price, 0, promo]], dtype=float)
    x_weekend = np.array([[price, 1, promo]], dtype=float)
    q = (1-weekend_prob)*model.predict(x_weekday)[0] + weekend_prob*model.predict(x_weekend)[0]
    return max(0.0, float(q))