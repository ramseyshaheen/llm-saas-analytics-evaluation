import duckdb
import anthropic
import os
import re
import sys
from dotenv import load_dotenv

# CONFIG

"""
Usage:
python scripts/evaluate_metric.py mrr detailed
python scripts/evaluate_metric.py churn minimal
"""

if len(sys.argv) != 3:
    print("Usage: python evaluate_metric.py <metric> <variant>")
    sys.exit(1)

metric = sys.argv[1]          # mrr | churn | nrr | decomposition
variant = sys.argv[2]         # minimal | explicit | detailed

MODEL = "claude-sonnet-4-5-20250929"
DB_PATH = "saas_analytics.duckdb"
PROMPT_PATH = f"prompts/{metric}/{variant}.txt"

# LOAD ENV/CLIENT

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# LOAD PROMPT

with open(PROMPT_PATH, "r") as f:
    prompt = f.read()

SCHEMA_CONTEXT = """
You are an analytics engineer working with a SaaS dataset.

Tables:

customers(customer_id, customer_name, signup_date, country, segment)
plans(plan_id, plan_name, monthly_price, billing_period)
subscriptions(subscription_id, customer_id, plan_id, start_date, end_date, status)
invoices(invoice_id, subscription_id, invoice_date, amount, paid_date)
usage_events(event_id, customer_id, event_date, event_type, usage_units)
"""

# CALL CLAUDE API

response = client.messages.create(
    model=MODEL,
    max_tokens=1500,
    messages=[
        {"role": "user", "content": SCHEMA_CONTEXT},
        {"role": "user", "content": prompt}
    ]
)

raw_output = response.content[0].text

print("\n--- Claude Raw Output ---\n")
print(raw_output)

# EXTRACT SQL

sql_complete_match = re.search(r"```sql\s*(.*?)\s*```", raw_output, re.DOTALL)
sql_start_match = re.search(r"```sql\s*(.*)", raw_output, re.DOTALL)

sql = None
sql_status = None

if sql_complete_match:
    sql = sql_complete_match.group(1).strip()
    sql_status = "complete"
elif sql_start_match:
    sql = sql_start_match.group(1).strip()
    sql_status = "incomplete"
else:
    sql_status = "missing"

print("\n--- SQL Extraction Status ---")
print(f"Status: {sql_status}")

if not sql or sql_status != "complete":
    print("\n--- SQL EXECUTION SKIPPED ---")
    sys.exit(1)

print("\n--- Extracted SQL ---\n")
print(sql)

# EXECUTE SQL

con = duckdb.connect(DB_PATH)

try:
    result_df = con.execute(sql).fetchdf()
    print("\n--- Query Result ---\n")
    print(result_df)
except Exception as e:
    print("\n--- SQL EXECUTION FAILED ---")
    raise e

# METRIC SPECIFIC VALIDATION

def validate_decomposition(df):
    required = {"starting_mrr", "ending_mrr", "expansion_mrr", "contraction_mrr", "churn_mrr"}
    if not required.issubset(df.columns):
        print("\nWARNING: Missing decomposition columns.")
        return
    
    row = df.iloc[0]
    lhs = row["starting_mrr"] + row["expansion_mrr"] - row["contraction_mrr"] - row["churn_mrr"]
    rhs = row["ending_mrr"]
    print("\n--- Reconciliation Check ---")
    print(f"Calculated End = {lhs}")
    print(f"Reported End = {rhs}")
    print(f"Difference = {lhs - rhs}")

def validate_single_value(df):
    if df.shape[0] != 1:
        print("\nWARNING: Expected single-row output.")
    else:
        print("\nSingle-row output confirmed.")

if metric == "revenue_decomposition":
    validate_decomposition(result_df)
else:
    validate_single_value(result_df)
