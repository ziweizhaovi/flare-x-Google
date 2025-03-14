import time
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
from src.flare_ai_defai.ai_risk_analyzer import AIRiskAnalyzer
from typing import Optional

class BigQueryFetcher:
    def __init__(self, ai_analyzer: Optional[AIRiskAnalyzer] = None):
        self.client = bigquery.Client()
        self.last_check_time = datetime.utcnow()
        self.ai_analyzer = ai_analyzer

    def fetch_liquidity_pools(self):
        """
        Fetches liquidity pool data from major DEXes on Ethereum
        Returns a pandas DataFrame containing pool data
        """
        query = """
        WITH transactions_data AS (
  SELECT 
    t.block_timestamp, 
    t.hash AS transaction_hash,
    t.block_number,
    t.from_address AS trader, 
    t.to_address AS dex_contract,
    IF(CAST(t.value AS NUMERIC) / 1e18 = 0, NULL, CAST(t.value AS NUMERIC) / 1e18) AS eth_transferred, -- If ETH = 0, rely on token data
    t.gas * t.gas_price / 1e18 AS gas_fee_eth, -- Gas Fee in ETH
    t.gas_price / 1e9 AS gas_price_gwei, -- Gas Price in Gwei
    CASE 
      WHEN t.to_address = "0x8ad599c3A0FF1de082011eFDDc58F1908Eb6e6D8" THEN "Swap"  -- Uniswap ETH/USDC Pool
      WHEN t.to_address = "0xc36442b4a4522e871399cd717abdd847ab11fe88" -- Uniswap V3: Position Manager (Liquidity Add/Remove)
      THEN "Liquidity Event"
      ELSE NULL -- Exclude unknown transactions
    END AS transaction_type
  FROM `bigquery-public-data.crypto_ethereum.transactions` t
  WHERE t.to_address IN (
      "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",  -- Uniswap v2 Router
      "0xe592427a0aece92de3edee1f18e0157c05861564",  -- Uniswap v3 Router
      "0x8ad599c3A0FF1de082011eFDDc58F1908Eb6e6D8"  -- Uniswap ETH/USDC Pool
  )
  AND t.block_timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND transaction_type IS NOT NULL -- Remove "Unknown" transactions
),

tokens_data AS (
  SELECT 
    tok.transaction_hash,
    tok.from_address AS sender,
    tok.to_address AS receiver,
    tok.token_address,
    -- Normalize token values based on decimals
    CASE 
      WHEN tok.token_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48" THEN SAFE_CAST(tok.value AS BIGNUMERIC) / 1e6  -- USDC (6 decimals)
      WHEN tok.token_address = "0xC02aaa39b223FE8D0A0e5C4F27eAD9083C756Cc2" THEN SAFE_CAST(tok.value AS BIGNUMERIC) / 1e18 -- WETH (18 decimals)
      ELSE SAFE_CAST(tok.value AS BIGNUMERIC) / 1e18 -- Default to 18 decimals for other tokens
    END AS token_amount,
    COALESCE(tk.symbol, "Unknown Token") AS token_name -- Fetch token symbol if available
  FROM `bigquery-public-data.crypto_ethereum.token_transfers` tok
  LEFT JOIN `bigquery-public-data.crypto_ethereum.tokens` tk 
  ON tok.token_address = tk.address -- Match contract address to token name
  WHERE tok.transaction_hash IN (SELECT transaction_hash FROM transactions_data)
)

SELECT 
  td.block_timestamp,
  td.transaction_hash,
  td.block_number,
  td.trader, 
  td.dex_contract,
  COALESCE(td.eth_transferred, 0) AS eth_transferred, -- If ETH transfer is NULL, set it to 0
  COALESCE(tok.token_amount, 0) AS token_value_transferred, -- Individual token values instead of sum
  td.gas_fee_eth,
  td.gas_price_gwei,
  td.transaction_type,
  tok.token_name AS token_involved, -- Each row contains a single token name
  tok.token_address AS token_address -- Each row contains a single token address
FROM transactions_data td
LEFT JOIN tokens_data tok
ON td.transaction_hash = tok.transaction_hash
ORDER BY td.block_timestamp DESC
LIMIT 100;

        """
        query_job = self.client.query(query)
        return query_job.result().to_dataframe()

    def detect_liquidity_changes(self, df, threshold=0.2):
        """
        Detect significant liquidity changes in pools and analyze with AI
        """
        alerts = []
        
        for (token0, token1), group in df.groupby(['token0', 'token1']):
            sorted_group = group.sort_values('block_timestamp')
            if len(sorted_group) >= 2:
                old_reserve0 = sorted_group.iloc[0]['reserve0']
                new_reserve0 = sorted_group.iloc[-1]['reserve0']
                
                if old_reserve0 > 0:
                    change = (new_reserve0 - old_reserve0) / old_reserve0
                    if abs(change) >= threshold:
                        event_data = {
                            'token0': token0,
                            'token1': token1,
                            'change_percentage': change * 100,
                            'timestamp': sorted_group.iloc[-1]['block_timestamp']
                        }

                        # Add AI analysis if available
                        if self.ai_analyzer:
                            risk_score, analysis = self.ai_analyzer.analyze_liquidity_change(event_data)
                            event_data['risk_score'] = risk_score
                            event_data['analysis'] = analysis
                            event_data['risk_hash'] = self.ai_analyzer.generate_risk_hash(risk_score, analysis)

                        alerts.append(event_data)
        
        return alerts

    def start_monitoring(self, interval: int = 60):
        """
        Continuously monitors liquidity pools
        Args:
            interval (int): Time between checks in seconds
        """
        while True:
            try:
                df = self.fetch_liquidity_pools()
                if not df.empty:
                    alerts = self.detect_liquidity_changes(df)
                    if alerts:
                        print(f"⚠️ Found {len(alerts)} significant liquidity changes!")
                        for alert in alerts:
                            print(f"Pool {alert['token0']}/{alert['token1']}: {alert['change_percentage']:.2f}% change")
                
                time.sleep(interval)
            except Exception as e:
                print(f"Error monitoring pools: {e}")
                time.sleep(interval)

if __name__ == "__main__":
    # Example usage
    fetcher = BigQueryFetcher()
    fetcher.start_monitoring() 