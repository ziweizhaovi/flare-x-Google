import pandas as pd
import numpy as np

# Create sample data
n_samples = 10
data = {
    'transaction_hash': [f'0x{i:032x}' for i in range(n_samples)],
    'trader': [f'0x{i:040x}' for i in range(n_samples)],
    'eth_transferred': np.random.uniform(0, 10, n_samples),
    'token_value_transferred': np.random.uniform(0, 1000, n_samples),
    'gas_fee_eth': np.random.uniform(0.001, 0.01, n_samples),
    'gas_price_gwei': np.random.uniform(20, 100, n_samples)
}

df = pd.DataFrame(data)
df.to_csv('example_data.csv', index=False)
print("Sample data created in example_data.csv") 