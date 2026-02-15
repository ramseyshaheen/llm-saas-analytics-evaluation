# generate_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# CONFIG
NUM_CUSTOMERS = 500
TODAY = datetime.today()

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

random.seed(42)
np.random.seed(42)

# GENERATE PLANS
plans = pd.DataFrame([
    {"plan_id": 1, "plan_name": "Basic", "monthly_price": 50.00, "billing_period": "monthly"},
    {"plan_id": 2, "plan_name": "Pro", "monthly_price": 150.00, "billing_period": "monthly"},
    {"plan_id": 3, "plan_name": "Enterprise", "monthly_price": 500.00, "billing_period": "monthly"},
])

plans.to_parquet(f"{OUTPUT_DIR}/plans.parquet", index=False)

# GENERATE CUSTOMERS (customer size)
segments = ["SMB", "Mid-Market", "Enterprise"]
segment_weights = [0.6, 0.3, 0.1]

countries = ["US", "CA", "UK", "DE", "FR", "AU"]

customers = []

for customer_id in range(1, NUM_CUSTOMERS + 1):
    segment = random.choices(segments, weights=segment_weights, k=1)[0]

    # Segment-based signup age
    if segment == "Enterprise":
        days_ago = random.randint(900, 1800)
    elif segment == "Mid-Market":
        days_ago = random.randint(300, 1200)
    else:  # SMB
        days_ago = random.randint(30, 900)

    signup_date = TODAY - timedelta(days=days_ago)

    country = random.choice(countries)

    customers.append({
        "customer_id": customer_id,
        "customer_name": f"Customer {customer_id}",
        "signup_date": signup_date.date(),
        "country": country,
        "segment": segment
    })

customers_df = pd.DataFrame(customers)

customers_df.to_parquet(f"{OUTPUT_DIR}/customers.parquet", index=False)

print("Generated:")
print(f"- {len(customers_df)} customers")
print(f"- {len(plans)} plans")

# GENERATE SUBSCRIPTIONS
subscriptions = []
subscription_id = 1

for _, customer in customers_df.iterrows():
    segment = customer["segment"]
    signup_date = pd.to_datetime(customer["signup_date"])

    # Segment-based churn probability (smaller customer will be more likely to churn)
    if segment == "Enterprise":
        churn_prob = 0.08
    elif segment == "Mid-Market":
        churn_prob = 0.20
    else:  # SMB
        churn_prob = 0.35

    churned = random.random() < churn_prob

    # Initial plan choice
    if segment == "Enterprise":
        current_plan = 3
    elif segment == "Mid-Market":
        current_plan = random.choice([2, 3])
    else:
        current_plan = random.choice([1, 2])

    current_start = signup_date

    # Optional upgrade
    upgrade_happens = random.random() < 0.25

    if upgrade_happens and current_plan < 3:
        upgrade_offset_days = random.randint(90, 360)
        upgrade_date = current_start + timedelta(days=upgrade_offset_days)

        subscriptions.append({
            "subscription_id": subscription_id,
            "customer_id": customer["customer_id"],
            "plan_id": current_plan,
            "start_date": current_start.date(),
            "end_date": upgrade_date.date(),
            "status": "active"
        })

        subscription_id += 1
        current_plan += 1
        current_start = upgrade_date

    # Final state
    if churned:
        churn_offset_days = random.randint(120, 600)
        end_date = current_start + timedelta(days=churn_offset_days)

        subscriptions.append({
            "subscription_id": subscription_id,
            "customer_id": customer["customer_id"],
            "plan_id": current_plan,
            "start_date": current_start.date(),
            "end_date": end_date.date(),
            "status": "churned"
        })
    else:
        subscriptions.append({
            "subscription_id": subscription_id,
            "customer_id": customer["customer_id"],
            "plan_id": current_plan,
            "start_date": current_start.date(),
            "end_date": None,
            "status": "active"
        })

    subscription_id += 1

subscriptions_df = pd.DataFrame(subscriptions)
subscriptions_df.to_parquet(f"{OUTPUT_DIR}/subscriptions.parquet", index=False)

print(f"- {len(subscriptions_df)} subscriptions")


# GENERATE INVOICES
subscriptions_df = pd.read_parquet(f"{OUTPUT_DIR}/subscriptions.parquet")
plans_df = pd.read_parquet(f"{OUTPUT_DIR}/plans.parquet")

plan_price_lookup = dict(
    zip(plans_df["plan_id"], plans_df["monthly_price"])
)

invoices = []
invoice_id = 1

for _, sub in subscriptions_df.iterrows():
    start = pd.to_datetime(sub["start_date"])
    end = pd.to_datetime(sub["end_date"]) if pd.notnull(sub["end_date"]) else TODAY

    billing_months = max(1, int((end - start).days / 30))

    for m in range(billing_months):
        invoice_date = start + timedelta(days=30 * m)

        amount = plan_price_lookup[sub["plan_id"]]

        # Segment-based payment behavior 
        customer_segment = customers_df.loc[
            customers_df["customer_id"] == sub["customer_id"], "segment"
        ].values[0]

        if customer_segment == "SMB":
            late_prob = 0.25
            unpaid_prob = 0.10
        elif customer_segment == "Mid-Market":
            late_prob = 0.10
            unpaid_prob = 0.03
        else:
            late_prob = 0.05
            unpaid_prob = 0.01

        rand = random.random()

        if rand < unpaid_prob:
            paid_date = None
        elif rand < unpaid_prob + late_prob:
            paid_date = invoice_date + timedelta(days=random.randint(15, 45))
        else:
            paid_date = invoice_date + timedelta(days=random.randint(0, 5))

        invoices.append({
            "invoice_id": invoice_id,
            "subscription_id": sub["subscription_id"],
            "invoice_date": invoice_date.date(),
            "amount": amount,
            "paid_date": paid_date.date() if paid_date else None
        })

        invoice_id += 1

invoices_df = pd.DataFrame(invoices)
invoices_df.to_parquet(f"{OUTPUT_DIR}/invoices.parquet", index=False)

print(f"- {len(invoices_df)} invoices")

# GENERATE USAGE EVENTS
subscriptions_df = pd.read_parquet(f"{OUTPUT_DIR}/subscriptions.parquet")
customers_df = pd.read_parquet(f"{OUTPUT_DIR}/customers.parquet")

usage_events = []
event_id = 1

for _, customer in customers_df.iterrows():
    customer_id = customer["customer_id"]
    segment = customer["segment"]
    signup_date = pd.to_datetime(customer["signup_date"])

    # Base usage by segment
    if segment == "Enterprise":
        base_usage = 120
    elif segment == "Mid-Market":
        base_usage = 60
    else:
        base_usage = 25

    customer_subs = subscriptions_df[
        subscriptions_df["customer_id"] == customer_id
    ]

    for _, sub in customer_subs.iterrows():
        start = pd.to_datetime(sub["start_date"])
        end = pd.to_datetime(sub["end_date"]) if pd.notnull(sub["end_date"]) else TODAY

        current_date = start

        while current_date <= end:
            usage_multiplier = 1.0

            # Usage decay before churn
            if sub["status"] == "churned":
                days_to_churn = (end - current_date).days
                if days_to_churn < 90:
                    usage_multiplier *= 0.6

            # Noise
            noise = random.uniform(0.8, 1.2)

            usage_units = int(base_usage * usage_multiplier * noise)

            usage_events.append({
                "event_id": event_id,
                "customer_id": customer_id,
                "event_date": current_date.date(),
                "event_type": "product_usage",
                "usage_units": max(0, usage_units)
            })

            event_id += 1
            current_date += timedelta(days=30)

usage_df = pd.DataFrame(usage_events)
usage_df.to_parquet(f"{OUTPUT_DIR}/usage_events.parquet", index=False)

print(f"- {len(usage_df)} usage events")


