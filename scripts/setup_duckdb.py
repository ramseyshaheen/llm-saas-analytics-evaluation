import duckdb

# Create / connect to local DuckDB database
con = duckdb.connect("saas_analytics.duckdb")

# Load parquet files as tables
con.execute("""
CREATE OR REPLACE TABLE customers AS
SELECT * FROM read_parquet('data/customers.parquet');
""")

con.execute("""
CREATE OR REPLACE TABLE plans AS
SELECT * FROM read_parquet('data/plans.parquet');
""")

con.execute("""
CREATE OR REPLACE TABLE subscriptions AS
SELECT * FROM read_parquet('data/subscriptions.parquet');
""")

con.execute("""
CREATE OR REPLACE TABLE invoices AS
SELECT * FROM read_parquet('data/invoices.parquet');
""")

con.execute("""
CREATE OR REPLACE TABLE usage_events AS
SELECT * FROM read_parquet('data/usage_events.parquet');
""")

# Basic checks
tables = ["customers", "plans", "subscriptions", "invoices", "usage_events"]

for table in tables:
    count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count} rows")

con.close()
