# qa_generate_data
import pandas as pd

pd.read_parquet("data/usage_events.parquet").head()
pd.read_parquet("data/usage_events.parquet").describe()
