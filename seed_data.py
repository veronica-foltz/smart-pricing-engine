import numpy as np, pandas as pd, random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42); np.random.seed(42)
data_dir = Path("data"); data_dir.mkdir(exist_ok=True)

PRODUCT_NAMES = [
    "Espresso Shot","Cappuccino","Latte","Mocha","Cold Brew",
    "Blueberry Muffin","Chocolate Croissant","Banana Bread","Bagel w/ Cream Cheese","Cheesecake Slice",
    "Protein Bar","Trail Mix","Kettle Chips","Chocolate Bar","Granola Cup",
    "Spring Water 500ml","Sparkling Water 330ml","Orange Juice","Iced Tea",
    "Reusable Cup"
]

CATS = ["Coffee","Bakery","Snacks","Beverages","Merch"]

# realistic price bands per category
PRICE_BANDS = {
    "Coffee":    (2.50, 6.00),
    "Bakery":    (2.00, 5.00),
    "Snacks":    (1.00, 3.00),
    "Beverages": (1.00, 4.00),
    "Merch":     (8.00, 20.00),
}

def rand_price(lo, hi): return round(float(np.random.uniform(lo, hi)), 2)
def rand_cost(price):   return round(float(price * np.random.uniform(0.35, 0.65)), 2)

n_products = 20
prod_ids = [f"P{1000+i}" for i in range(n_products)]
names = [PRODUCT_NAMES[i % len(PRODUCT_NAMES)] for i in range(n_products)]
cats  = [random.choice(CATS) for _ in range(n_products)]

prices = []
costs  = []
for cat in cats:
    lo, hi = PRICE_BANDS[cat]
    p  = rand_price(lo, hi)
    c  = rand_cost(p)
    # cost must be < price
    if c >= p: c = round(p * 0.6, 2)
    prices.append(p)
    costs.append(c)

prods = pd.DataFrame({
    "product_id": prod_ids,
    "name": names,
    "category": cats,
    "unit_cost": costs,
    "current_price": prices,
    "sku": [f"SKU-{i:04d}" for i in range(n_products)]
})
prods.to_csv(data_dir/"products.csv", index=False)

# --- Sales history (60 days) with seasonality/promos ---
start = (datetime.today().date() - timedelta(days=60))
dates = [start + timedelta(days=i) for i in range(60)]
cat_base = {"Coffee":28, "Bakery":20, "Snacks":15, "Beverages":18, "Merch":6}

rows = []
for pid, pprice, pcost, cat in zip(prods["product_id"], prods["current_price"], prods["unit_cost"], prods["category"]):
    pop = np.random.uniform(0.7, 1.3)      # popularity
    elast = np.random.uniform(0.8, 1.6)    # price sensitivity
    for d in dates:
        weekend = d.weekday() in (5, 6)
        seasonal = (1.25 if weekend else 1.0) * np.random.uniform(0.9, 1.1)
        promo = np.random.rand() < 0.06
        price_today = float(pprice)
        if promo:
            price_today = round(max(pcost * 1.05, pprice * np.random.uniform(0.85, 0.95)), 2)
        margin_factor = max(0.5, min(2.5, (price_today / max(pcost, 0.01))))
        demand = cat_base[cat] * pop * seasonal * (elast / margin_factor) * (1.15 if promo else 1.0)
        units = int(np.random.poisson(max(0.2, demand)))
        rows.append({
            "date": d.isoformat(),
            "product_id": pid,
            "units_sold": units,
            "price_at_sale": price_today,
            "promo_flag": int(promo)
        })
pd.DataFrame(rows).to_csv(data_dir/"sales_history.csv", index=False)

# --- Inventory ---
pd.DataFrame({
    "product_id": prods["product_id"],
    "on_hand": np.random.randint(10, 200, n_products),
    "reorder_point": np.random.randint(10, 60, n_products),
    "lead_time_days": np.random.randint(2, 10, n_products)
}).to_csv(data_dir/"inventory.csv", index=False)

# --- Competitors (2 shops every ~3 days) ---
comp_rows = []
for pid, sku, our_price in zip(prods["product_id"], prods["sku"], prods["current_price"]):
    for d in dates[::3]:
        for c in ["ShopAlpha", "ShopBeta"]:
            cp = round(max(0.5, np.random.normal(our_price, max(0.05, our_price * 0.08))), 2)
            if np.random.rand() < 0.1:
                cp = round(our_price * np.random.uniform(0.80, 0.92), 2)
            comp_rows.append({
                "date": d.isoformat(),
                "product_id": pid,
                "sku": sku,
                "competitor": c,
                "competitor_price": cp
            })
pd.DataFrame(comp_rows).to_csv(data_dir/"competitors.csv", index=False)

print("Wrote realistic CSVs to", data_dir.resolve())
print(prods[["product_id","name","category","unit_cost","current_price"]].head(10).to_string(index=False))