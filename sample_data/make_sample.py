"""Generates a deliberately messy sales dataset to demo the agent."""
import numpy as np, pandas as pd
rng = np.random.default_rng(7)
n = 600
dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 540, n), unit="D")
region = rng.choice(["East", "West", "North", "South"], n)
cat = rng.choice(["Furniture", "Technology", "Office Supplies"], n, p=[.25, .3, .45])
qty = rng.integers(1, 10, n)
price = rng.uniform(5, 400, n).round(2)
sales = (qty * price).round(2)
profit = (sales * rng.normal(0.12, 0.15, n)).round(2)
df = pd.DataFrame({"Order ID": [f"ORD-{i:05d}" for i in range(n)],
                   "Order Date": dates.strftime("%Y-%m-%d"), "Customer Name": [f"Customer {i%150}" for i in range(n)],
                   "Email": [f"user{i%150}@mail.com" for i in range(n)], "Region": region, "Category": cat,
                   "Quantity": qty, "Sales": sales, "Profit": profit})
df.loc[rng.choice(n, 25, replace=False), "Region"] = " east "
df.loc[rng.choice(n, 20, replace=False), "Region"] = "WEST"
df.loc[rng.choice(n, 20, replace=False), "Category"] = "technology"
df.loc[rng.choice(n, 30, replace=False), "Sales"] = np.nan
df.loc[rng.choice(n, 15, replace=False), "Quantity"] = np.nan
df.loc[rng.choice(n, 8, replace=False), "Quantity"] = -3
df.loc[rng.choice(n, 5, replace=False), "Sales"] = 250000
df["Sales"] = df["Sales"].astype("object")
df.loc[rng.choice(n, 10, replace=False), "Sales"] = "1,250.50"
df.loc[rng.choice(n, 10, replace=False), "Order Date"] = "not available"
df = pd.concat([df, df.sample(12, random_state=1)], ignore_index=True)
df.to_csv("sample_data/messy_sales.csv", index=False)
print("saved", df.shape)
